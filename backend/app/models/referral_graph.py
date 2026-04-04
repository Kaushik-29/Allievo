import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class ReferralGraph(Base):
    __tablename__ = "referral_graph"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referrer_worker_id = Column(UUID(as_uuid=True), ForeignKey("workers.id"), nullable=True)
    referred_worker_id = Column(UUID(as_uuid=True), ForeignKey("workers.id"), unique=True, nullable=False)
    referred_at = Column(DateTime(timezone=True), default=datetime.utcnow)
