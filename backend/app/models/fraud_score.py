import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Numeric, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class FraudScore(Base):
    __tablename__ = "fraud_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("workers.id"), nullable=False)
    total_score = Column(Numeric(4, 2), nullable=False)              # 0.0 – 1.0

    # Individual signal scores
    gps_trajectory_score = Column(Numeric(4, 2), nullable=True)
    cell_tower_match = Column(Boolean, nullable=True)
    platform_activity_score = Column(Numeric(4, 2), nullable=True)
    device_fp_match = Column(Boolean, nullable=True)
    zone_presence_score = Column(Numeric(4, 2), nullable=True)      # GPS_days_in_zone_last_30 / 30
    accelerometer_score = Column(Numeric(4, 2), nullable=True)
    claim_freq_score = Column(Numeric(4, 2), nullable=True)

    # Ring signals
    device_ring_flag = Column(Boolean, default=False)
    upi_cluster_flag = Column(Boolean, default=False)
    temporal_burst_flag = Column(Boolean, default=False)
    referral_chain_flag = Column(Boolean, default=False)
    gps_proximity_flag = Column(Boolean, default=False)
    ring_signals_count = Column(Integer, default=0)

    # Outcome
    action_taken = Column(String(20), nullable=True)                 # 'auto_approve'|'partial'|'hold'|'block'
    baseline_adjustment = Column(Numeric(4, 2), default=0.0)        # downward adjustment for repeat FP
    scored_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    claim = relationship("Claim", back_populates="fraud_scores")
    worker = relationship("Worker", back_populates="fraud_scores")
