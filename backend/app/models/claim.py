import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class Claim(Base):
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("workers.id"), nullable=False)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), nullable=False)
    trigger_event_id = Column(UUID(as_uuid=True), ForeignKey("trigger_events.id"), nullable=False)
    dae_used = Column(Numeric(10, 2), nullable=False)               # DAE at time of claim
    disruption_hours = Column(Numeric(5, 2), nullable=False)
    working_hours = Column(Numeric(5, 2), nullable=False, default=8.0)
    coverage_factor = Column(Numeric(4, 2), nullable=False)
    severity_multiplier = Column(Numeric(4, 2), nullable=False)
    gross_payout = Column(Numeric(10, 2), nullable=False)           # pre-cap calculation
    capped_payout = Column(Numeric(10, 2), nullable=False)          # after weekly + aggregate caps
    status = Column(String(20), default="pending")                  # 'pending'|'approved'|'partial'|'held'|'blocked'|'paid'
    auto_generated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    platform_scope = Column(String(20), nullable=True)              # 'all'|'zomato'|'swiggy'
    calculation_log = Column(JSONB, nullable=True)                  # full formula trace for audit

    worker = relationship("Worker", back_populates="claims")
    policy = relationship("Policy", back_populates="claims")
    trigger_event = relationship("TriggerEvent", back_populates="claims")
    fraud_scores = relationship("FraudScore", back_populates="claim", cascade="all, delete-orphan")
    payouts = relationship("Payout", back_populates="claim")
