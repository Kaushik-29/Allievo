"""GPS Cleanup Worker — runs daily at 03:00 IST (DPDP compliance)."""
import logging
from datetime import datetime, timedelta
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.gps_cleanup.cleanup_old_gps_pings")
def cleanup_old_gps_pings():
    """
    Delete all gps_pings WHERE pinged_at < NOW() - 90 days.
    DPDP Act compliance — GPS data is a sensitive personal data category.
    """
    from app.models.gps_ping import GpsPing

    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=settings.GPS_RETENTION_DAYS)
        deleted = db.query(GpsPing).filter(GpsPing.pinged_at < cutoff).delete()
        db.commit()
        logger.info(f"GPS cleanup: deleted {deleted} ping records older than {settings.GPS_RETENTION_DAYS} days")
    except Exception as e:
        logger.error(f"GPS cleanup error: {e}")
        db.rollback()
    finally:
        db.close()
