from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict


class ClaimResponse(BaseModel):
    id: UUID
    worker_id: UUID
    policy_id: UUID
    trigger_event_id: UUID
    dae_used: float
    disruption_hours: float
    working_hours: float
    coverage_factor: float
    severity_multiplier: float
    gross_payout: float
    capped_payout: float
    status: str
    auto_generated_at: datetime
    platform_scope: Optional[str] = None
    calculation_log: Optional[Dict] = None

    model_config = ConfigDict(from_attributes=True)


class ClaimAppeal(BaseModel):
    was_working: bool
    note: str
