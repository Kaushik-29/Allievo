from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date


class PolicyBase(BaseModel):
    worker_id: UUID
    tier: str


class PolicyResponse(PolicyBase):
    id: UUID
    week_start: date
    week_end: date
    premium_paid: float
    status: str
    max_weekly_payout: float
    coverage_hours_day: int
    eligible_for_payout: bool
    loyalty_weeks: int
    waiting_weeks_done: int

    model_config = ConfigDict(from_attributes=True)
