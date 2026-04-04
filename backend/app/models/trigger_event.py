import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class TriggerEvent(Base):
    __tablename__ = "trigger_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trigger_type = Column(String(30), nullable=False)   # 'rainfall'|'heat'|'aqi'|'curfew'|'outage'
    zone_id = Column(UUID(as_uuid=True), ForeignKey("zone_scores.id"), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_hours = Column(Numeric(5, 2), nullable=True)
    severity_level = Column(String(20), nullable=True)  # 'low'|'moderate'|'high'|'severe'
    severity_multiplier = Column(Numeric(4, 2), nullable=False)
    raw_value = Column(Numeric(10, 2), nullable=True)   # mm/hr, AQI, temp °C, etc.
    source_api = Column(String(50), nullable=True)      # 'imd'|'openweathermap'|'cpcb'|'govt'
    secondary_confirmed = Column(Boolean, default=False)
    order_drop_pct = Column(Numeric(5, 2), nullable=True)  # % order drop observed in zone
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    zone = relationship("ZoneScore", back_populates="trigger_events")
    claims = relationship("Claim", back_populates="trigger_event")
    ring_alerts = relationship("RingAlert", back_populates="trigger_event")
