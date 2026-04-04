"""
Trigger Poll Worker — runs every 15 minutes via Celery Beat.
"""
import logging
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.trigger_poll.poll_all_triggers", bind=True, max_retries=3)
def poll_all_triggers(self):
    """
    Poll all 5 trigger types across all active zones.
    For each trigger detected, fire the payout pipeline.
    """
    from app.services.trigger_monitor import TriggerMonitor
    from app.services.payout_pipeline import PayoutPipeline
    from app.models.trigger_event import TriggerEvent

    db = SessionLocal()
    try:
        monitor = TriggerMonitor(db)
        results = monitor.poll_all_zones()

        for result in results:
            # Create trigger_event record
            trigger = TriggerEvent(
                trigger_type=result.trigger_type,
                zone_id=result.zone_id,
                started_at=__import__("datetime").datetime.utcnow(),
                duration_hours=result.duration_hours,
                severity_level=result.severity_level,
                severity_multiplier=result.severity_multiplier,
                raw_value=result.raw_value,
                source_api=result.source_api,
                secondary_confirmed=result.secondary_confirmed,
                order_drop_pct=result.order_drop_pct,
                is_active=True,
            )
            db.add(trigger)
            db.commit()
            db.refresh(trigger)

            logger.info(f"Trigger event created: {trigger.id} ({result.trigger_type})")

            # Fire payout pipeline as a background task
            process_trigger_payout.delay(str(trigger.id))

        db.commit()
        logger.info(f"Trigger poll completed: {len(results)} triggers detected")
    except Exception as exc:
        logger.error(f"Trigger poll error: {exc}")
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@celery_app.task(name="app.workers.trigger_poll.process_trigger_payout", bind=True, max_retries=2)
def process_trigger_payout(self, trigger_event_id: str):
    """Process payout pipeline for a single trigger event."""
    from app.services.payout_pipeline import PayoutPipeline

    db = SessionLocal()
    try:
        pipeline = PayoutPipeline(db)
        pipeline.process_trigger_event(trigger_event_id)
    except Exception as exc:
        logger.error(f"Payout pipeline error for {trigger_event_id}: {exc}")
        raise self.retry(exc=exc, countdown=120)
    finally:
        db.close()
