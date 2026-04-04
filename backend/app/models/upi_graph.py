import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class UpiGraph(Base):
    __tablename__ = "upi_graph"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("workers.id"), nullable=False)
    upi_vpa = Column(String(100), nullable=False)
    registered_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_payout_at = Column(DateTime(timezone=True), nullable=True)
    is_primary = Column(Boolean, default=True)

    worker = relationship("Worker", back_populates="upi_entries")
