from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


class TriggerEventResponse(BaseModel):
    id: UUID
    trigger_type: str
    zone_id: Optional[UUID] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_hours: Optional[float] = None
    severity_level: Optional[str] = None
    severity_multiplier: float
    raw_value: Optional[float] = None
    source_api: Optional[str] = None
    secondary_confirmed: bool
    order_drop_pct: Optional[float] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
