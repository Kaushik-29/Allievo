"""
WorkerPlan — tracks which plan a worker is currently enrolled in.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class WorkerPlan(Base):
    __tablename__ = "worker_plans"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id        = Column(UUID(as_uuid=True), ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_name        = Column(String(20), nullable=False)                # basic | dynamic | premium
    enrolled_at      = Column(DateTime(timezone=True), default=datetime.utcnow)
    weekly_premium   = Column(Numeric(8, 2), nullable=False)            # stored at enrollment; refreshed Sunday for dynamic
    status           = Column(String(20), default="active")             # active | paused | cancelled
    waiting_ends_at  = Column(DateTime(timezone=True), nullable=True)   # enrolled_at + 28 days
    eligible_for_payout = Column(Boolean, default=False)                # True after 28-day wait

    # Relationships
    worker = relationship("Worker", back_populates="worker_plans")

    def to_dict(self) -> dict:
        return {
            "id":               str(self.id),
            "worker_id":        str(self.worker_id),
            "plan_name":        self.plan_name,
            "enrolled_at":      self.enrolled_at.isoformat() if self.enrolled_at else None,
            "weekly_premium":   float(self.weekly_premium),
            "status":           self.status,
            "waiting_ends_at":  self.waiting_ends_at.isoformat() if self.waiting_ends_at else None,
            "eligible_for_payout": self.eligible_for_payout,
        }
