"""
Reconciliation Worker — runs every 6 hours.
Checks and releases held partial payouts.
"""
import logging
from datetime import datetime, timedelta
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.reconciliation.run_reconciliation")
def run_reconciliation():
    """
    Query: payouts WHERE payout_type='partial_second'
                   AND release_status='pending'
                   AND release_scheduled_at < NOW() - 24 hours
    """
    from app.models.payout import Payout

    db = SessionLocal()
    try:
        now = datetime.utcnow()
        overdue_threshold = now - timedelta(hours=settings.PARTIAL_RELEASE_HOURS)
        crisis_threshold = now - timedelta(hours=settings.OVERDUE_ESCALATION_HOURS)

        overdue_payouts = (
            db.query(Payout)
            .filter(
                Payout.payout_type == "partial_second",
                Payout.release_status == "pending",
                Payout.release_scheduled_at < overdue_threshold,
            )
            .all()
        )

        released = 0
        escalated = 0

        for payout in overdue_payouts:
            payout.reconciliation_checked_at = now

            # Check for new fraud signals since original scoring
            new_fraud_signals = _check_new_fraud_signals(db, payout)

            if not new_fraud_signals:
                # Release held amount
                from app.services.payout_pipeline import PayoutPipeline
                pipeline = PayoutPipeline(db)
                pipeline.initiate_upi_transfer(
                    str(payout.id), float(payout.amount), payout.upi_vpa
                )
                payout.release_status = "released"
                released += 1
            else:
                payout.release_status = "escalated"
                escalated += 1
                logger.warning(f"Payout {payout.id} escalated — new fraud signals found")

            # Auto-escalate if overdue > 26 hours
            if payout.release_scheduled_at and payout.release_scheduled_at < crisis_threshold:
                if payout.release_status == "pending":
                    payout.release_status = "escalated"
                    escalated += 1
                    logger.error(f"CRISIS: Payout {payout.id} overdue > 26 hours — auto-escalating")

            db.commit()

        logger.info(f"Reconciliation: {released} released, {escalated} escalated out of {len(overdue_payouts)} checked")
    except Exception as e:
        logger.error(f"Reconciliation error: {e}")
    finally:
        db.close()


@celery_app.task(name="app.workers.reconciliation.release_held_payout")
def release_held_payout(payout_id: str):
    """Release a specific held payout (called via schedule_partial_release)."""
    from app.models.payout import Payout
    from app.services.payout_pipeline import PayoutPipeline

    db = SessionLocal()
    try:
        payout = db.query(Payout).filter(Payout.id == payout_id).first()
        if not payout:
            return

        payout.reconciliation_checked_at = datetime.utcnow()
        new_signals = _check_new_fraud_signals(db, payout)

        if not new_signals:
            pipeline = PayoutPipeline(db)
            pipeline.initiate_upi_transfer(str(payout.id), float(payout.amount), payout.upi_vpa)
            payout.release_status = "released"
        else:
            payout.release_status = "escalated"
            logger.warning(f"Held payout {payout_id} escalated on release check")

        db.commit()
    except Exception as e:
        logger.error(f"Release held payout error: {e}")
    finally:
        db.close()


def _check_new_fraud_signals(db, payout) -> bool:
    """
    Check if any new fraud signals have appeared since original scoring.
    Returns True if new signals found that should block release.
    """
    from app.models.fraud_score import FraudScore

    latest_score = (
        db.query(FraudScore)
        .filter(FraudScore.claim_id == payout.claim_id)
        .order_by(FraudScore.scored_at.desc())
        .first()
    )

    if not latest_score:
        return False

    # Check ring signals that appeared after original scoring
    return (
        latest_score.device_ring_flag or
        latest_score.upi_cluster_flag or
        latest_score.gps_proximity_flag
    )
