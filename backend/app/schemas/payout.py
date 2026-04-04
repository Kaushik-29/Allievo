from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


class PayoutResponse(BaseModel):
    id: UUID
    claim_id: UUID
    worker_id: UUID
    upi_vpa: str
    amount: float
    payout_type: str
    status: str
    initiated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    release_scheduled_at: Optional[datetime] = None
    release_status: Optional[str] = None
    failure_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
