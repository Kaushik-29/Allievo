import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Integer, Numeric, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class EarningsSnapshot(Base):
    __tablename__ = "earnings_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(20), nullable=False)              # 'zomato' | 'swiggy' | 'other'
    snapshot_date = Column(Date, nullable=False)
    total_settlements = Column(Numeric(10, 2), nullable=False) # net earnings after commission
    active_days_count = Column(Integer, nullable=False)        # days with >=1 completed delivery
    dae_single = Column(Numeric(10, 2), nullable=False)        # total_settlements / active_days
    dae_confidence_adj = Column(Numeric(10, 2), nullable=False) # cold-start adjusted DAE
    raw_days_available = Column(Integer, nullable=False)       # raw days of data available
    fetched_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    worker = relationship("Worker", back_populates="earnings_snapshots")
