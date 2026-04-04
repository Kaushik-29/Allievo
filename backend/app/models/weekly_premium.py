"""
WeeklyPremium — stores the computed dynamic premium for each Sunday computation.
Only populated for 'dynamic' plan workers.
"""
import uuid
from datetime import datetime, date
from sqlalchemy import Column, Numeric, DateTime, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class WeeklyPremium(Base):
    __tablename__ = "weekly_premiums"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id         = Column(UUID(as_uuid=True), ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_name         = Column(String(20), nullable=False, default="dynamic")
    week_start        = Column(Date, nullable=False)                   # Monday
    premium_amount    = Column(Numeric(8, 2), nullable=False)
    week_risk_score   = Column(Numeric(5, 4), nullable=True)
    peak_rain_mm      = Column(Numeric(6, 2), nullable=True)
    peak_temp_c       = Column(Numeric(5, 1), nullable=True)
    peak_aqi          = Column(Numeric(6, 1), nullable=True)
    multiplier_applied = Column(Numeric(6, 4), nullable=True)
    plain_reason      = Column(Text, nullable=True)                   # human-readable notification text
    computed_at       = Column(DateTime(timezone=True), default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id":               str(self.id),
            "worker_id":        str(self.worker_id),
            "plan_name":        self.plan_name,
            "week_start":       str(self.week_start),
            "premium_amount":   float(self.premium_amount),
            "week_risk_score":  float(self.week_risk_score) if self.week_risk_score else None,
            "peak_rain_mm":     float(self.peak_rain_mm) if self.peak_rain_mm else None,
            "peak_temp_c":      float(self.peak_temp_c) if self.peak_temp_c else None,
            "peak_aqi":         float(self.peak_aqi) if self.peak_aqi else None,
            "multiplier_applied": float(self.multiplier_applied) if self.multiplier_applied else None,
            "plain_reason":     self.plain_reason,
            "computed_at":      self.computed_at.isoformat() if self.computed_at else None,
        }
