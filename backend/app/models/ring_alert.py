import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, ARRAY, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class RingAlert(Base):
    __tablename__ = "ring_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trigger_event_id = Column(UUID(as_uuid=True), ForeignKey("trigger_events.id"), nullable=False)
    worker_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)   # array of flagged worker IDs
    device_ids = Column(ARRAY(Text), nullable=True)                   # shared hardware IDs
    upi_vpas = Column(ARRAY(Text), nullable=True)                     # clustered UPI destinations
    signals_fired = Column(ARRAY(Text), nullable=False)               # list of ring signals triggered
    signal_count = Column(Integer, nullable=False)
    status = Column(String(20), default="open")                       # 'open'|'reviewing'|'resolved'
    resolution = Column(String(20), nullable=True)                    # 'fraud_confirmed'|'legitimate'|'partial'
    human_reviewer_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    trigger_event = relationship("TriggerEvent", back_populates="ring_alerts")
