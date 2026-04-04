import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.core.database import Base


class GpsPing(Base):
    __tablename__ = "gps_pings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(UUID(as_uuid=True), ForeignKey("workers.id", ondelete="CASCADE"), nullable=False)
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    accuracy_meters = Column(Numeric(6, 2), nullable=True)
    speed_kmh = Column(Numeric(5, 2), nullable=True)
    altitude = Column(Numeric(7, 2), nullable=True)
    cell_tower_lat = Column(Numeric(10, 7), nullable=True)
    cell_tower_lng = Column(Numeric(10, 7), nullable=True)
    cell_tower_matches = Column(Boolean, nullable=True)  # GPS vs tower within 500m?
    pinged_at = Column(DateTime(timezone=True), nullable=False)
    session_id = Column(String(64), nullable=True)

    worker = relationship("Worker", back_populates="gps_pings")
