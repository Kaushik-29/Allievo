import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, Numeric, Date, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Policy(Base):
    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zone_scores.id"), nullable=True)
    tier = Column(String(20), nullable=False)                           # 'basic' | 'standard' | 'premium'
    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)                             # week_start + 6 days
    premium_paid = Column(Numeric(8, 2), nullable=False)
    static_base_premium = Column(Numeric(8, 2), nullable=False)
    risk_score_at_issue = Column(Numeric(4, 2), nullable=False)
    seasonal_factor = Column(Numeric(4, 2), nullable=False)
    loyalty_weeks = Column(Integer, nullable=False, default=0)
    loyalty_adjustment = Column(Numeric(4, 2), nullable=False)
    status = Column(String(20), default="active")                      # 'active'|'expired'|'cancelled'
    max_weekly_payout = Column(Numeric(8, 2), nullable=False)          # 400 | 700 | 1000
    coverage_hours_day = Column(Integer, nullable=False)               # 4 | 6 | 8
    coverage_factor = Column(Numeric(4, 2), nullable=False)            # 0.7 | 1.0 | 1.3
    waiting_weeks_done = Column(Integer, nullable=False, default=0)
    eligible_for_payout = Column(Boolean, default=False)               # TRUE after 4 consecutive weeks
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    worker = relationship("Worker", back_populates="policies")
    zone = relationship("ZoneScore", back_populates="policies")
    claims = relationship("Claim", back_populates="policy")
