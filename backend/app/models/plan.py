"""
Plan model — defines the 3 insurance plans (basic / dynamic / premium).
This is a static catalogue table; rows are seeded once.
"""
import uuid
from sqlalchemy import Column, String, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Plan(Base):
    __tablename__ = "plans"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name           = Column(String(20), unique=True, nullable=False)   # basic | dynamic | premium
    days_per_week  = Column(Integer, nullable=False)                    # 2 | 3 | 4
    hours_per_day  = Column(Integer, nullable=False)                    # 2 | 4 | 6
    covered_hours  = Column(Integer, nullable=False)                    # days*hours: 4 | 12 | 24
    premium_rate   = Column(Numeric(5, 4), nullable=True)               # NULL for dynamic (computed)
    claim_mode     = Column(String(30), nullable=False)                 # manual_or_auto | auto_only
    plan_value     = Column(Numeric(10, 2), nullable=False)             # hourly_rate * covered_hours
    max_payout     = Column(Numeric(10, 2), nullable=False)             # same as plan_value
    description    = Column(Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id":            str(self.id),
            "name":          self.name,
            "days_per_week": self.days_per_week,
            "hours_per_day": self.hours_per_day,
            "covered_hours": self.covered_hours,
            "premium_rate":  float(self.premium_rate) if self.premium_rate else None,
            "claim_mode":    self.claim_mode,
            "plan_value":    float(self.plan_value),
            "max_payout":    float(self.max_payout),
            "description":   self.description,
        }
