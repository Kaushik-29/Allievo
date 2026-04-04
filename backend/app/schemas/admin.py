from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List


class RingAlertResponse(BaseModel):
    id: UUID
    trigger_event_id: UUID
    worker_ids: List[UUID]
    device_ids: Optional[List[str]] = None
    upi_vpas: Optional[List[str]] = None
    signals_fired: List[str]
    signal_count: int
    status: str
    resolution: Optional[str] = None
    human_reviewer_id: Optional[UUID] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RingAlertResolve(BaseModel):
    resolution: str
