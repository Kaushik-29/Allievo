import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.core.database import Base


class ZoneScore(Base):
    __tablename__ = "zone_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_name = Column(String(100), nullable=False)
    city = Column(String(50), nullable=False)
    zone_boundary = Column(Geometry("POLYGON", srid=4326), nullable=True)  # PostGIS polygon
    risk_multiplier = Column(Numeric(4, 2), nullable=False)        # 0.8 – 1.8
    seasonal_factor = Column(Numeric(4, 2), default=1.0)           # 1.0 – 1.4
    disruption_days_yr = Column(Numeric(6, 2), nullable=False)     # rolling 3-year average
    risk_score_current = Column(Numeric(4, 2), nullable=True)      # 0.05 – 0.95
    hist_risk = Column(Numeric(4, 2), nullable=True)
    weather_risk = Column(Numeric(4, 2), nullable=True)
    pollution_risk = Column(Numeric(4, 2), nullable=True)
    traffic_risk = Column(Numeric(4, 2), nullable=True)
    live_event_risk = Column(Numeric(4, 2), nullable=True)
    zone_type = Column(String(20), nullable=True)                   # 'flood' | 'aqi' | 'low'
    last_scored_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    policies = relationship("Policy", back_populates="zone")
    trigger_events = relationship("TriggerEvent", back_populates="zone")
