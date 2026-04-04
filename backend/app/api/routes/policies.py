"""Policies API — /api/v1/policies"""
from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.core.config import settings
from app.models.policy import Policy
from app.models.zone_score import ZoneScore
from app.models.earnings_snapshot import EarningsSnapshot
from app.services.premium_engine import PremiumEngine
from app.services.weather_service import WeatherService
from app.services.curfew_service import CurfewService

router = APIRouter(prefix="/policies", tags=["policies"])
pe = PremiumEngine()
ws = WeatherService()
cs = CurfewService()


def check_enrollment_allowed(zone_type: str, month: int, is_renewal: bool) -> tuple[bool, str]:
    """
    Returns (allowed: bool, reason: str) per Section 6.
    Renewals are always allowed.
    """
    if is_renewal:
        return True, "renewal always allowed"

    if zone_type == "flood" and month in [6, 7, 8, 9]:
        return False, "New enrollment paused June–September in flood-risk zones"

    if zone_type == "aqi" and month in [10, 11, 12, 1, 2]:
        return False, "New enrollment paused Oct–Feb in AQI-risk zones"

    return True, "enrollment allowed"


def check_payout_eligibility(worker_id: str, db: Session) -> tuple[bool, int]:
    """
    Count consecutive weeks of paid policies.
    Returns (eligible, consecutive_weeks).
    RULE: >= 4 consecutive weeks required.
    """
    policies = (
        db.query(Policy)
        .filter(Policy.worker_id == worker_id, Policy.status.in_(["active", "expired"]))
        .order_by(Policy.week_start.desc())
        .all()
    )

    consecutive_weeks = 0
    prev_week_end = None

    for policy in policies:
        if prev_week_end is None:
            prev_week_end = policy.week_end
            consecutive_weeks = 1
        else:
            # Check continuity: gap between policies must be 0 days
            gap = (prev_week_end - policy.week_end).days
            if gap == 7:  # consecutive weeks
                consecutive_weeks += 1
                prev_week_end = policy.week_end
            else:
                break  # gap found — stop counting

    return consecutive_weeks >= settings.WAITING_PERIOD_WEEKS, consecutive_weeks


@router.get("/current/{worker_id}")
def get_current_policy(
    worker_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Current active policy for a worker."""
    policy = (
        db.query(Policy)
        .filter(Policy.worker_id == worker_id, Policy.status == "active")
        .order_by(Policy.week_start.desc())
        .first()
    )
    if not policy:
        raise HTTPException(status_code=404, detail="No active policy")
    return _policy_to_dict(policy)


@router.get("/next-premium/{worker_id}")
def get_next_premium(
    worker_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Preview next week's premium before renewal."""
    from app.models.worker import Worker

    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    current_policy = (
        db.query(Policy)
        .filter(Policy.worker_id == worker_id, Policy.status == "active")
        .order_by(Policy.week_start.desc())
        .first()
    )
    if not current_policy:
        raise HTTPException(status_code=404, detail="No active policy to renew")

    zone = db.query(ZoneScore).filter(ZoneScore.id == current_policy.zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    next_week_start = date.today() + timedelta(days=(7 - date.today().weekday()))
    month = next_week_start.month
    loyalty_weeks = current_policy.loyalty_weeks + 1

    zmr = pe.zone_risk_multiplier(float(zone.disruption_days_yr))
    seasonal = pe.seasonal_buffer_factor(zone.zone_type or "low", month)
    sbp = pe.static_base_premium(zmr, current_policy.tier, loyalty_weeks, seasonal)
    
    # Dynamically inject real-time Open-Meteo API & Curfew detection
    forecast = ws.get_7d_risk_forecast()
    civil_risk = cs.check_curfew(zone.city or "Bengaluru")
    
    live_risk = pe.compute_risk_score(
        disruption_days_last_365=int(zone.disruption_days_yr),
        rain_probability_7d=forecast["rain_probability_7d"],
        rain_severity_factor=forecast["rain_severity_factor"],
        aqi_7day_avg=150.0,
        avg_zone_speed_kmh=18.0,
        live_event_score=1.0 if civil_risk["curfew_active"] else 0.0,
    )
    rs = live_risk["risk_score"]
    
    next_premium = pe.weekly_premium(sbp, rs, loyalty_weeks)

    return {
        "next_premium": next_premium,
        "tier": current_policy.tier,
        "week_start": str(next_week_start),
        "week_end": str(next_week_start + timedelta(days=6)),
        "max_payout": pe.TIER_MAX_PAYOUT[current_policy.tier],
        "risk_score": rs,
    }


@router.post("/renew")
def renew_policy(
    worker_id: UUID,
    tier: str = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Worker opts in for next week. Returns new policy."""
    from app.models.worker import Worker

    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    current_policy = (
        db.query(Policy)
        .filter(Policy.worker_id == worker_id, Policy.status == "active")
        .order_by(Policy.week_start.desc())
        .first()
    )

    is_renewal = current_policy is not None
    use_tier = tier or (current_policy.tier if current_policy else "standard")

    zone = None
    if current_policy:
        zone = db.query(ZoneScore).filter(ZoneScore.id == current_policy.zone_id).first()

    if not zone:
        raise HTTPException(status_code=400, detail="No zone assigned. Complete onboarding first.")

    # Check enrollment restrictions
    today = date.today()
    allowed, reason = check_enrollment_allowed(zone.zone_type or "low", today.month, is_renewal)
    if not allowed:
        raise HTTPException(status_code=403, detail=reason)

    loyalty_weeks = (current_policy.loyalty_weeks + 1) if current_policy else 0

    zmr = pe.zone_risk_multiplier(float(zone.disruption_days_yr))
    seasonal = pe.seasonal_buffer_factor(zone.zone_type or "low", today.month)
    sbp = pe.static_base_premium(zmr, use_tier, loyalty_weeks, seasonal)
    
    # Calculate live Risk Score on Renewal using current real API forecast & Curfew detection
    forecast = ws.get_7d_risk_forecast()
    civil_risk = cs.check_curfew(zone.city or "Bengaluru")
    
    live_risk = pe.compute_risk_score(
        disruption_days_last_365=int(zone.disruption_days_yr),
        rain_probability_7d=forecast["rain_probability_7d"],
        rain_severity_factor=forecast["rain_severity_factor"],
        aqi_7day_avg=150.0,
        avg_zone_speed_kmh=18.0,
        live_event_score=1.0 if civil_risk["curfew_active"] else 0.0,
    )
    rs = live_risk["risk_score"]
    
    premium = pe.weekly_premium(sbp, rs, loyalty_weeks)

    next_week_start = today + timedelta(days=(7 - today.weekday()))
    week_end = next_week_start + timedelta(days=6)

    eligible, consecutive_weeks = check_payout_eligibility(str(worker_id), db)

    new_policy = Policy(
        worker_id=worker_id,
        zone_id=zone.id,
        tier=use_tier,
        week_start=next_week_start,
        week_end=week_end,
        premium_paid=premium,
        static_base_premium=sbp,
        risk_score_at_issue=rs,
        seasonal_factor=seasonal,
        loyalty_weeks=loyalty_weeks,
        loyalty_adjustment=pe.loyalty_adjustment(loyalty_weeks),
        status="active",
        max_weekly_payout=pe.TIER_MAX_PAYOUT[use_tier],
        coverage_hours_day=pe.TIER_COVERAGE_HOURS[use_tier],
        coverage_factor=pe.TIER_COVERAGE_FACTOR[use_tier],
        waiting_weeks_done=consecutive_weeks,
        eligible_for_payout=eligible,
    )
    db.add(new_policy)
    db.commit()
    db.refresh(new_policy)
    return _policy_to_dict(new_policy)


@router.get("/history/{worker_id}")
def get_policy_history(
    worker_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Full policy history for a worker."""
    policies = (
        db.query(Policy)
        .filter(Policy.worker_id == worker_id)
        .order_by(Policy.week_start.desc())
        .all()
    )
    return [_policy_to_dict(p) for p in policies]


@router.get("/tiers")
def get_tiers():
    """Return tier definitions with current configuration."""
    return {
        "tiers": [
            {
                "name": "basic",
                "weekly_premium_range": {"min": 30, "max": 56},
                "max_payout": pe.TIER_MAX_PAYOUT["basic"],
                "coverage_hours": pe.TIER_COVERAGE_HOURS["basic"],
                "coverage_factor": pe.TIER_COVERAGE_FACTOR["basic"],
            },
            {
                "name": "standard",
                "weekly_premium_range": {"min": 30, "max": 70},
                "max_payout": pe.TIER_MAX_PAYOUT["standard"],
                "coverage_hours": pe.TIER_COVERAGE_HOURS["standard"],
                "coverage_factor": pe.TIER_COVERAGE_FACTOR["standard"],
                "recommended": True,
            },
            {
                "name": "premium",
                "weekly_premium_range": {"min": 42, "max": 100},
                "max_payout": pe.TIER_MAX_PAYOUT["premium"],
                "coverage_hours": pe.TIER_COVERAGE_HOURS["premium"],
                "coverage_factor": pe.TIER_COVERAGE_FACTOR["premium"],
            },
        ]
    }


@router.post("/change-tier")
def change_tier(
    worker_id: UUID,
    new_tier: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Change tier for next policy cycle."""
    if new_tier not in ["basic", "standard", "premium"]:
        raise HTTPException(status_code=400, detail="Invalid tier")
    current_policy = (
        db.query(Policy)
        .filter(Policy.worker_id == worker_id, Policy.status == "active")
        .order_by(Policy.week_start.desc())
        .first()
    )
    if not current_policy:
        raise HTTPException(status_code=404, detail="No active policy to change tier on")
    return {"message": f"Tier will change to '{new_tier}' on next renewal", "effective_week": str(current_policy.week_end + timedelta(days=1))}


def _policy_to_dict(p: Policy) -> dict:
    return {
        "id": str(p.id),
        "tier": p.tier,
        "week_start": str(p.week_start),
        "week_end": str(p.week_end),
        "premium_paid": float(p.premium_paid),
        "status": p.status,
        "max_weekly_payout": float(p.max_weekly_payout),
        "coverage_hours_day": p.coverage_hours_day,
        "eligible_for_payout": p.eligible_for_payout,
        "loyalty_weeks": p.loyalty_weeks,
        "waiting_weeks_done": p.waiting_weeks_done,
        "risk_score_at_issue": float(p.risk_score_at_issue),
    }
