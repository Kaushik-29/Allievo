from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "allievo",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.workers.trigger_poll",
        "app.workers.premium_recalc",
        "app.workers.reconciliation",
        "app.workers.gps_cleanup",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# ─── Periodic Task Schedule (Celery Beat) ────────────────────────────────────
celery_app.conf.beat_schedule = {
    # Poll all triggers every 15 minutes
    "poll-triggers-15min": {
        "task": "app.workers.trigger_poll.poll_all_triggers",
        "schedule": 900,  # 900 seconds = 15 minutes
    },
    # Sunday premium recalculation at 22:00 IST
    "sunday-premium-recalc": {
        "task": "app.workers.premium_recalc.sunday_premium_recalc",
        "schedule": crontab(hour=22, minute=0, day_of_week="sunday"),
    },
    # Reconciliation every 6 hours
    "reconciliation-6h": {
        "task": "app.workers.reconciliation.run_reconciliation",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    # GPS cleanup daily at 03:00 IST
    "gps-cleanup-daily": {
        "task": "app.workers.gps_cleanup.cleanup_old_gps_pings",
        "schedule": crontab(hour=3, minute=0),
    },
}
