"""Workers API — /api/v1/workers"""
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.core.database import get_db
from app.core.security import create_access_token, encrypt_token
from app.models.worker import Worker
from app.models.device_fingerprint import DeviceFingerprint
from app.models.earnings_snapshot import EarningsSnapshot
from app.models.upi_graph import UpiGraph
from app.services.earnings_engine import EarningsEngine
from app.services.otp_service import ProfileOtpService

router = APIRouter(prefix="/workers", tags=["workers"])
earnings_engine = EarningsEngine()
otp_service = ProfileOtpService()

class UpdateRequest(BaseModel):
    field: str # 'phone' | 'email'
    value: str

class VerifyUpdate(BaseModel):
    field: str
    otp: str

class GeneralUpdate(BaseModel):
    name: Optional[str] = None
    upi_id: Optional[str] = None
    primary_platform: Optional[str] = None
    work_location: Optional[str] = None
    current_location: Optional[str] = None
    working_proof: Optional[str] = None
    city: Optional[str] = None




@router.post("/link-platform")
def link_platform(
    worker_id: UUID,
    platform: str,
    oauth_code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Link Zomato or Swiggy via OAuth. Triggers earnings fetch."""
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    # Mock OAuth token exchange in development
    mock_token = f"mock_token_{platform}_{worker_id}"
    encrypted = encrypt_token(mock_token)

    if platform == "zomato":
        worker.zomato_linked = True
        worker.zomato_token = encrypted
    elif platform == "swiggy":
        worker.swiggy_linked = True
        worker.swiggy_token = encrypted
    else:
        raise HTTPException(status_code=400, detail="Platform must be 'zomato' or 'swiggy'")

    db.commit()

    # Fetch earnings (mock for Phase 1)
    snapshot = _fetch_and_store_earnings(worker_id=str(worker_id), platform=platform, db=db)
    return {"linked": True, "platform": platform, "dae": snapshot.get("dae_confidence_adj")}


@router.get("/{worker_id}/profile")
def get_worker_profile(
    worker_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Full worker profile + current policy status."""
    from app.models.policy import Policy
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    current_policy = (
        db.query(Policy)
        .filter(Policy.worker_id == worker_id, Policy.status == "active")
        .order_by(Policy.week_start.desc())
        .first()
    )

    return {
        "id": str(worker.id),
        "name": worker.name,
        "username": worker.username,
        "phone": worker.phone,
        "email": worker.email,
        "city": worker.city,
        "aadhar_no": worker.aadhar_no,
        "pan_no": worker.pan_no,
        "upi_id": worker.upi_id,
        "primary_platform": worker.primary_platform,
        "work_location": worker.work_location,
        "current_location": worker.current_location,
        "working_proof": worker.working_proof,
        "language_pref": worker.language_pref,
        "zomato_linked": worker.zomato_linked,
        "swiggy_linked": worker.swiggy_linked,
        "onboarded_at": worker.onboarded_at.isoformat() if worker.onboarded_at else None,
        "current_policy": {
            "id": str(current_policy.id),
            "tier": current_policy.tier,
            "week_start": str(current_policy.week_start),
            "week_end": str(current_policy.week_end),
            "premium_paid": float(current_policy.premium_paid),
            "eligible_for_payout": current_policy.eligible_for_payout,
            "max_weekly_payout": float(current_policy.max_weekly_payout),
        } if current_policy else None,
    }

@router.post("/profile/update-request")
def request_profile_update(
    data: UpdateRequest, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """Starts an OTP-secured update for Phone/Email."""
    # current_user['sub'] is the worker_id
    otp_service.request_otp(current_user["sub"], data.field, data.value)
    return {"message": f"OTP sent for {data.field} change (check console)."}

@router.post("/profile/update-verify")
def verify_profile_update(
    data: VerifyUpdate, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """Finalizes the update after OTP verification."""
    new_value = otp_service.verify_otp(current_user["sub"], data.field, data.otp)
    if not new_value:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")
        
    worker = db.query(Worker).filter(Worker.id == current_user["sub"]).first()
    if data.field == "phone":
        worker.phone = new_value
    elif data.field == "email":
        worker.email = new_value
    
    db.commit()
    return {"message": f"{data.field.capitalize()} updated successfully."}

@router.patch("/profile")
def update_profile_general(
    data: GeneralUpdate, 
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """Update non-sensitive fields directly."""
    worker = db.query(Worker).filter(Worker.id == current_user["sub"]).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
        
    for field, value in data.dict(exclude_unset=True).items():
        setattr(worker, field, value)
        
    db.commit()
    return {"message": "Profile updated successfully.", "worker": {"name": worker.name, "city": worker.city}}



@router.get("/{worker_id}/earnings")
def get_worker_earnings(
    worker_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get current DAE breakdown across all platforms."""
    snapshots = db.query(EarningsSnapshot).filter(EarningsSnapshot.worker_id == worker_id).all()
    if not snapshots:
        return {"combined_dae": 0, "platforms": []}

    platform_daes = {s.platform: float(s.dae_confidence_adj) for s in snapshots}
    combined = earnings_engine.compute_combined_dae(platform_daes)

    return {
        "combined_dae": combined,
        "platforms": [
            {
                "platform": s.platform,
                "dae_raw": float(s.dae_single),
                "dae_adjusted": float(s.dae_confidence_adj),
                "active_days": s.active_days_count,
                "snapshot_date": str(s.snapshot_date),
            }
            for s in snapshots
        ],
    }


@router.get("/{worker_id}/zone-presence")
def get_zone_presence(
    worker_id: UUID,
    zone_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """30-day zone presence score."""
    from app.services.fraud_gate import FraudGate
    fg = FraudGate(db)
    zps = fg.compute_zone_presence_score(str(worker_id), str(zone_id))
    return {"zone_presence_score": zps, "worker_id": str(worker_id), "zone_id": str(zone_id)}


@router.post("/dpdp-consent")
def record_dpdp_consent(
    worker_id: UUID,
    gps_consent: bool,
    device_consent: bool,
    platform_consent: bool,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Record DPDP consent with scope. All 3 must be True to proceed."""
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    worker.dpdp_consent_at = datetime.utcnow()
    worker.dpdp_consent_scope = {"gps": gps_consent, "device": device_consent, "platform": platform_consent}
    db.commit()
    return {"consent_recorded": True, "all_granted": all([gps_consent, device_consent, platform_consent])}


@router.delete("/{worker_id}")
def request_data_deletion(
    worker_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """DPDP data deletion request. 30-day hold if open claims."""
    from app.models.claim import Claim
    open_claims = (
        db.query(Claim)
        .filter(Claim.worker_id == worker_id, Claim.status.in_(["pending", "held", "partial"]))
        .count()
    )
    if open_claims > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete: {open_claims} open claim(s). Data will be deleted after 30-day hold period.",
        )
    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if worker:
        worker.is_active = False
    db.commit()
    return {"deletion_queued": True, "effective_date": (datetime.utcnow() + timedelta(days=30)).isoformat()}


def _fetch_and_store_earnings(worker_id: str, platform: str, db) -> dict:
    """Fetch mock earnings and store snapshot."""
    from datetime import date
    import random
    # Mock: generate 90 days of earnings
    rng = __import__("random").Random(hash(worker_id + platform))
    settlements = [rng.uniform(300, 900) for _ in range(90)]
    active_days = rng.randint(45, 80)

    result = earnings_engine.compute_dae(settlements, active_days)

    existing = db.query(EarningsSnapshot).filter(
        EarningsSnapshot.worker_id == worker_id,
        EarningsSnapshot.platform == platform,
    ).first()

    if existing:
        existing.total_settlements = sum(settlements)
        existing.active_days_count = active_days
        existing.dae_single = result["dae_raw"]
        existing.dae_confidence_adj = result["dae_adjusted"]
        existing.raw_days_available = 90
        existing.snapshot_date = date.today()
    else:
        snap = EarningsSnapshot(
            worker_id=worker_id,
            platform=platform,
            snapshot_date=date.today(),
            total_settlements=sum(settlements),
            active_days_count=active_days,
            dae_single=result["dae_raw"],
            dae_confidence_adj=result["dae_adjusted"],
            raw_days_available=90,
        )
        db.add(snap)

    db.commit()
    return result
