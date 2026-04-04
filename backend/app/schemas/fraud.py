from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


class FraudScoreResponse(BaseModel):
    id: UUID
    claim_id: UUID
    worker_id: UUID
    total_score: float
    gps_trajectory_score: Optional[float] = None
    cell_tower_match: Optional[bool] = None
    platform_activity_score: Optional[float] = None
    device_fp_match: Optional[bool] = None
    zone_presence_score: Optional[float] = None
    accelerometer_score: Optional[float] = None
    claim_freq_score: Optional[float] = None
    device_ring_flag: bool
    upi_cluster_flag: bool
    temporal_burst_flag: bool
    referral_chain_flag: bool
    gps_proximity_flag: bool
    ring_signals_count: int
    action_taken: Optional[str] = None
    baseline_adjustment: float
    scored_at: datetime

    model_config = ConfigDict(from_attributes=True)
