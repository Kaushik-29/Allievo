"""
Premium Recalculation Worker — runs every Sunday at 22:00 IST.
"""
import logging
from datetime import datetime, timedelta, date
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.premium_recalc.sunday_premium_recalc")
def sunday_premium_recalc():
    """
    1. Fetch 7-day forecast data for each zone.
    2. Recompute risk scores.
    3. Update zone_scores.risk_score_current.
    4. For each renewing worker, compute next week's premium.
    5. Send Monday morning notification.
    6. Refresh stale earnings snapshots.
    """
    from app.models.zone_score import ZoneScore
    from app.models.policy import Policy
    from app.models.worker import Worker
    from app.models.earnings_snapshot import EarningsSnapshot
    from app.services.premium_engine import PremiumEngine
    from app.services.notification_service import NotificationService
    from app.services.weather_service import WeatherService
    from app.services.curfew_service import CurfewService

    db = SessionLocal()
    pe = PremiumEngine()
    ns = NotificationService()
    ws = WeatherService()
    cs = CurfewService()

    try:
        now = datetime.utcnow()
        today = now.date()

        # ── Step 1–3: Recompute risk scores for all zones
        zones = db.query(ZoneScore).all()
        
        # Fetch real-time grid weather forecast natively
        forecast = ws.get_7d_risk_forecast()
        
        for zone in zones:
            risk_data = pe.compute_risk_score(
                disruption_days_last_365=int(zone.disruption_days_yr or 5),
                rain_probability_7d=forecast["rain_probability_7d"],
                rain_severity_factor=forecast["rain_severity_factor"],
                aqi_7day_avg=150.0,         # TODO: fetch from CPCB
                avg_zone_speed_kmh=18.0,    # TODO: fetch from traffic API
                live_event_score=1.0 if cs.check_curfew(zone.city or "Bengaluru")["curfew_active"] else 0.0,
            )
            zone.risk_score_current = risk_data["risk_score"]
            zone.hist_risk = risk_data["components"]["historical"]
            zone.weather_risk = risk_data["components"]["weather"]
            zone.pollution_risk = risk_data["components"]["pollution"]
            zone.traffic_risk = risk_data["components"]["traffic"]
            zone.live_event_risk = risk_data["components"]["live_event"]
            zone.last_scored_at = now

        db.commit()
        logger.info(f"Risk scores updated for {len(zones)} zones")

        # ── Step 4–5: Notify renewing workers
        next_week_start = today + timedelta(days=(7 - today.weekday()))
        renewal_policies = (
            db.query(Policy)
            .filter(
                Policy.week_end >= today,
                Policy.week_end <= today + timedelta(days=7),
                Policy.status == "active",
            )
            .all()
        )

        for policy in renewal_policies:
            worker = db.query(Worker).filter(Worker.id == policy.worker_id).first()
            if not worker:
                continue

            zone = db.query(ZoneScore).filter(ZoneScore.id == policy.zone_id).first()
            if not zone:
                continue

            zmr = pe.zone_risk_multiplier(float(zone.disruption_days_yr or 5))
            month = next_week_start.month
            seasonal = pe.seasonal_buffer_factor(zone.zone_type or "low", month)
            sbp = pe.static_base_premium(zmr, policy.tier, policy.loyalty_weeks + 1, seasonal)
            rs = float(zone.risk_score_current or 0.2)
            next_premium = pe.weekly_premium(sbp, rs, policy.loyalty_weeks + 1)

            tier_config = pe.get_tier_config(policy.tier)

            ns.send_premium_renewal_notification(
                worker=worker,
                premium=next_premium,
                tier=policy.tier,
                max_payout=tier_config["max_payout"],
                premium_reason="Based on next week's risk forecast.",
            )

        # ── Step 6: Refresh stale earnings snapshots
        stale_cutoff = today - timedelta(days=30)
        stale_workers = (
            db.query(Worker)
            .filter(Worker.is_active == True)
            .join(EarningsSnapshot, EarningsSnapshot.worker_id == Worker.id, isouter=True)
            .filter(
                (EarningsSnapshot.snapshot_date == None) |
                (EarningsSnapshot.snapshot_date < stale_cutoff)
            )
            .all()
        )

        for worker in stale_workers:
            refresh_earnings_snapshot.delay(str(worker.id))

        logger.info(f"Premium recalc complete: {len(renewal_policies)} renewal notifications, {len(stale_workers)} earnings refreshes queued")
    except Exception as e:
        logger.error(f"Premium recalc error: {e}")
    finally:
        db.close()


@celery_app.task(name="app.workers.premium_recalc.refresh_earnings_snapshot")
def refresh_earnings_snapshot(worker_id: str):
    """Fetch fresh earnings data from platform APIs for a worker."""
    logger.info(f"[MOCK] Refreshing earnings for worker {worker_id}")
    # In production: call Zomato/Swiggy Partner APIs
