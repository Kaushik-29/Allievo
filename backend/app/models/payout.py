import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Payout(Base):
    __tablename__ = "payouts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("workers.id"), nullable=False)
    upi_vpa = Column(String(100), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payout_type = Column(String(20), nullable=False)                # 'full'|'partial_first'|'partial_second'
    status = Column(String(20), default="pending")                  # 'pending'|'initiated'|'success'|'failed'
    razorpay_transfer_id = Column(String(100), nullable=True)
    initiated_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    release_scheduled_at = Column(DateTime(timezone=True), nullable=True)  # for partial_second holds
    release_status = Column(String(20), nullable=True)              # 'pending'|'released'|'escalated'
    reconciliation_checked_at = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    claim = relationship("Claim", back_populates="payouts")
    worker = relationship("Worker", back_populates="payouts")
