import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class DeviceFingerprint(Base):
    __tablename__ = "device_fingerprints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    hardware_id_hash = Column(String(64), nullable=False)    # SHA-256 of Android Device ID
    sim_carrier = Column(String(50), nullable=True)
    fingerprint_js_id = Column(String(128), nullable=True)   # FingerprintJS Pro visitor ID
    captured_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    session_type = Column(String(20), nullable=True)         # 'onboarding' | 'session'
    is_current = Column(Boolean, default=True)

    worker = relationship("Worker", back_populates="device_fingerprints")
