"""Claims API — /api/v1/claims"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.models.claim import Claim
from app.models.payout import Payout
from app.models.trigger_event import TriggerEvent
from app.models.fraud_score import FraudScore
from app.schemas.claim import ClaimAppeal

router = APIRouter(prefix="/claims", tags=["claims"])


@router.get("/{worker_id}/claims")
def get_worker_claims(
    worker_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """All claims for a worker."""
    claims = (
        db.query(Claim)
        .filter(Claim.worker_id == worker_id)
        .order_by(Claim.auto_generated_at.desc())
        .all()
    )
    result = []
    for c in claims:
        # Get payout info
        latest_payout = db.query(Payout).filter(Payout.claim_id == c.id).order_by(Payout.created_at.desc()).first()
        fs = db.query(FraudScore).filter(FraudScore.claim_id == c.id).first()
        trigger_type = c.trigger_event.trigger_type if c.trigger_event else "Unknown"
        result.append({
            "id": str(c.id),
            "trigger_type": trigger_type,
            "trigger_event": trigger_type,
            "date": str(c.auto_generated_at.date()),
            "status": c.status,
            "capped_payout": float(c.capped_payout),
            "gross_payout": float(c.gross_payout),
            "dae_used": float(c.dae_used),
            "disruption_hours": float(c.disruption_hours),
            "severity_multiplier": float(c.severity_multiplier),
            "fraud_score": float(fs.total_score) if fs else None,
            "fraud_band": fs.action_taken if fs else None,
            "payout_status": latest_payout.status if latest_payout else None,
            "payout_amount": float(latest_payout.amount) if latest_payout else None,
            "razorpay_ref": latest_payout.razorpay_transfer_id if latest_payout else None,
            "release_at": str(latest_payout.release_scheduled_at) if latest_payout and latest_payout.release_scheduled_at else None,
        })
    return result


@router.get("/{claim_id}")
def get_claim_detail(
    claim_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Single claim detail with fraud score breakdown."""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    fs = db.query(FraudScore).filter(FraudScore.claim_id == claim_id).first()

    return {
        "id": str(claim.id),
        "status": claim.status,
        "calculation": claim.calculation_log,
        "amount": float(claim.capped_payout),
        "fraud_score": float(fs.total_score) if fs else None,
        "fraud_action_taken": fs.action_taken if fs else None,
    }


@router.get("/{worker_id}/active-event")
def get_active_event(
    worker_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Currently active disruption event in worker's zone."""
    from app.models.policy import Policy
    policy = db.query(Policy).filter(Policy.worker_id == worker_id, Policy.status == "active").first()
    if not policy or not policy.zone_id:
        return {"active_event": None}

    trigger = (
        db.query(TriggerEvent)
        .filter(TriggerEvent.zone_id == policy.zone_id, TriggerEvent.is_active == True)
        .first()
    )

    if not trigger:
        return {"active_event": None}

    return {
        "active_event": {
            "type": trigger.trigger_type,
            "started_at": str(trigger.started_at),
            "severity": trigger.severity_level,
        }
    }


@router.post("/{claim_id}/appeal")
def submit_appeal(
    claim_id: UUID,
    appeal: ClaimAppeal,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Submit appeal for held or blocked claims."""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    if claim.status not in ["held", "blocked"]:
        raise HTTPException(status_code=400, detail="Only held or blocked claims can be appealed")

    if len(appeal.note) > 100:
        raise HTTPException(status_code=400, detail="Note must be 100 characters max")

    # In a full flow, this would create an Appeal record. For Phase 1 we log it.
    import logging
    logging.info(f"Appeal received for {claim_id}: working={appeal.was_working}, note={appeal.note}")

    return {"message": "Appeal submitted successfully", "review_expected_in": "48 hours"}


@router.get("/{worker_id}/payout-status")
def get_payout_status(
    worker_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Current payout status + 'where's my remaining?' data."""
    payouts = (
        db.query(Payout)
        .filter(Payout.worker_id == worker_id)
        .order_by(Payout.created_at.desc())
        .limit(10)
        .all()
    )
    result = []
    for p in payouts:
        res = {
            "id": str(p.id),
            "amount": float(p.amount),
            "payout_type": p.payout_type,
            "status": p.status,
            "release_scheduled_at": str(p.release_scheduled_at) if p.release_scheduled_at else None,
            "release_status": p.release_status,
        }
        result.append(res)
    return result
