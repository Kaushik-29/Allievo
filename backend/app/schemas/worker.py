from typing import Optional, Dict
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class WorkerBase(BaseModel):
    phone: str
    name: str
    city: str
    language_pref: Optional[str] = "en"


class WorkerCreate(WorkerBase):
    pass


class WorkerResponse(WorkerBase):
    id: UUID
    zomato_linked: bool
    swiggy_linked: bool
    onboarded_at: Optional[datetime] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class DPDPCOnsent(BaseModel):
    gps_consent: bool
    device_consent: bool
    platform_consent: bool
