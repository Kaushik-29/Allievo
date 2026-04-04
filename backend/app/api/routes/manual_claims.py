"""
Manual Claims API — /api/v1/manual-claims
Worker-filed claims with proof, reason, and auto-verification.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user, get_admin_user
from app.models.manual_claim import ManualClaim
from app.models.worker import Worker
from app.models.worker_plan import WorkerPlan
from app.services.claim_verifier import auto_verify_claim, haversine_km

router = APIRouter(prefix="/manual-claims", tags=["manual-claims"])

VALID_DISRUPTION_TYPES = ["rainfall", "heat", "aqi", "curfew", "outage", "other"]


# ─────────────────────────────────────────────────────────────────
# REQUEST / RESPONSE SCHEMAS
# ─────────────────────────────────────────────────────────────────

class FileClaim(BaseModel):
    disruption_type:    str = Field(..., description="rainfall|heat|aqi|curfew|outage|other")
    disruption_date:    str = Field(..., description="ISO datetime of when disruption occurred")
    disruption_hours:   float = Field(..., ge=0.5, le=12.0, description="Hours of work lost (0.5–12)")
    description:        str = Field(..., min_length=20, max_length=1000)
    proof_text:         Optional[str] = Field(None, max_length=2000)
    proof_type:         Optional[str] = Field(None)          # screenshot | order_history | media | other
    declared_was_working: bool = Field(True)
    worker_lat:         Optional[float] = None
    worker_lon:         Optional[float] = None


class AdminDecision(BaseModel):
    decision:   str = Field(..., description="approved | denied")
    admin_note: str = Field("", max_length=500)
    payout_amount: Optional[float] = None


# ─────────────────────────────────────────────────────────────────
# WORKER ROUTES
# ─────────────────────────────────────────────────────────────────

@router.post("/file")
def file_claim(
    body: FileClaim,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    POST /api/v1/manual-claims/file
    Worker files a manual claim with reason + proof.
    Auto-verification runs immediately.
    """
    worker_id = current_user["sub"]

    if body.disruption_type not in VALID_DISRUPTION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid disruption_type. Must be one of: {VALID_DISRUPTION_TYPES}"
        )

    worker = db.query(Worker).filter(Worker.id == worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    # Parse disruption date
    try:
        disruption_dt = datetime.fromisoformat(body.disruption_date)
        if disruption_dt.tzinfo is None:
            disruption_dt = disruption_dt.replace(tzinfo=timezone.utc)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid disruption_date format. Use ISO format.")

    # Must not be in the future
    if disruption_dt > datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Disruption date cannot be in the future")

    # Get worker's active plan
    active_plan = (
        db.query(WorkerPlan)
        .filter(WorkerPlan.worker_id == worker_id, WorkerPlan.status == "active")
        .order_by(WorkerPlan.enrolled_at.desc())
        .first()
    )

    # Compute distance from registered zone
    dist_km = None
    within_15km = None
    if worker.registered_lat and worker.registered_lon and body.worker_lat and body.worker_lon:
        dist_km = haversine_km(
            float(worker.registered_lat), float(worker.registered_lon),
            body.worker_lat, body.worker_lon,
        )
        within_15km = dist_km <= 15.0

    # Create claim record
    claim = ManualClaim(
        worker_id=worker_id,
        disruption_type=body.disruption_type,
        disruption_date=disruption_dt,
        disruption_hours=body.disruption_hours,
        description=body.description,
        proof_text=body.proof_text,
        proof_type=body.proof_type,
        declared_was_working=body.declared_was_working,
        worker_lat=body.worker_lat,
        worker_lon=body.worker_lon,
        worker_registered_lat=float(worker.registered_lat) if worker.registered_lat else None,
        worker_registered_lon=float(worker.registered_lon) if worker.registered_lon else None,
        distance_from_zone_km=round(dist_km, 3) if dist_km else None,
        within_15km_radius=within_15km,
        plan_name=active_plan.plan_name if active_plan else "basic",
        hourly_rate=80.0,
        status="pending",
    )
    db.add(claim)
    db.flush()  # get the ID without committing

    # Run auto-verification
    verification = auto_verify_claim(claim, worker, db)

    # Update claim with verification results
    claim.auto_score    = verification["score"]
    claim.auto_result   = verification["result"]
    claim.auto_checks   = verification["checks"]
    claim.auto_reason   = verification["reason"]
    claim.estimated_payout = verification["estimated_payout"]

    # Set initial status based on auto result
    if verification["result"] == "auto_approve":
        claim.status = "auto_approved"
    elif verification["result"] == "auto_deny":
        claim.status = "auto_denied"
    else:
        claim.status = "under_review"

    db.commit()
    db.refresh(claim)

    return {
        "message": _status_message(claim.status),
        "claim": claim.to_dict(),
        "auto_verification": {
            "score":    verification["score"],
            "result":   verification["result"],
            "reason":   verification["reason"],
            "checks":   verification["checks"],
        },
    }


def _status_message(status: str) -> str:
    return {
        "auto_approved": "✅ Claim auto-approved! Payout will be processed.",
        "auto_denied":   "❌ Claim could not be verified automatically. Please appeal.",
        "under_review":  "⏳ Claim submitted for admin review. You'll hear back in 24–48 hrs.",
    }.get(status, "Claim submitted.")


@router.get("/my/{worker_id}")
def get_my_claims(
    worker_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """GET /api/v1/manual-claims/my/{worker_id} — all claims filed by this worker."""
    claims = (
        db.query(ManualClaim)
        .filter(ManualClaim.worker_id == worker_id)
        .order_by(ManualClaim.submitted_at.desc())
        .all()
    )
    return {"claims": [c.to_dict() for c in claims]}


@router.get("/{claim_id}")
def get_claim(
    claim_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """GET /api/v1/manual-claims/{claim_id} — single claim detail."""
    claim = db.query(ManualClaim).filter(ManualClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim.to_dict()


# ─────────────────────────────────────────────────────────────────
# ADMIN ROUTES
# ─────────────────────────────────────────────────────────────────

@router.get("/admin/queue")
def admin_claim_queue(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_admin_user),
):
    """
    GET /api/v1/manual-claims/admin/queue?status=under_review
    Admin views all manual claims, optionally filtered by status.
    """
    q = db.query(ManualClaim)
    if status:
        q = q.filter(ManualClaim.status == status)
    else:
        # Default: show pending + under_review first
        q = q.order_by(
            ManualClaim.status.in_(["under_review", "auto_approved"]).desc(),
            ManualClaim.submitted_at.desc(),
        )

    claims = q.order_by(ManualClaim.submitted_at.desc()).limit(100).all()

    # Enrich with worker name
    enriched = []
    for c in claims:
        d = c.to_dict()
        w = db.query(Worker).filter(Worker.id == c.worker_id).first()
        d["worker_name"] = w.name if w else "Unknown"
        d["worker_phone"] = w.phone if w else None
        d["worker_city"] = w.city if w else None
        enriched.append(d)

    return {
        "total": len(enriched),
        "claims": enriched,
        "summary": {
            "auto_approved": sum(1 for c in claims if c.status == "auto_approved"),
            "under_review":  sum(1 for c in claims if c.status == "under_review"),
            "auto_denied":   sum(1 for c in claims if c.status == "auto_denied"),
            "approved":      sum(1 for c in claims if c.status == "approved"),
            "denied":        sum(1 for c in claims if c.status == "denied"),
        }
    }


@router.post("/admin/{claim_id}/decide")
def admin_decide(
    claim_id: UUID,
    body: AdminDecision,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_admin_user),
):
    """
    POST /api/v1/manual-claims/admin/{claim_id}/decide
    Admin approves or denies a claim under review.
    """
    if body.decision not in ["approved", "denied"]:
        raise HTTPException(status_code=400, detail="decision must be 'approved' or 'denied'")

    claim = db.query(ManualClaim).filter(ManualClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    if claim.status not in ["under_review", "auto_approved", "auto_denied"]:
        raise HTTPException(
            status_code=400,
            detail=f"Claim status is '{claim.status}' — only under_review / auto claims can be decided"
        )

    claim.status       = body.decision
    claim.admin_note   = body.admin_note
    claim.admin_id     = admin.get("sub", "admin")
    claim.reviewed_at  = datetime.now(timezone.utc)
    if body.payout_amount is not None:
        claim.payout_amount = body.payout_amount
    elif body.decision == "approved" and claim.estimated_payout:
        claim.payout_amount = claim.estimated_payout

    db.add(claim)
    db.commit()
    db.refresh(claim)

    return {
        "message": f"Claim {body.decision}",
        "claim": claim.to_dict(),
    }


@router.post("/admin/{claim_id}/re-verify")
def admin_re_verify(
    claim_id: UUID,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_admin_user),
):
    """Re-run automatic verification (useful after worker provides more info)."""
    claim = db.query(ManualClaim).filter(ManualClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    worker = db.query(Worker).filter(Worker.id == claim.worker_id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    verification = auto_verify_claim(claim, worker, db)

    claim.auto_score  = verification["score"]
    claim.auto_result = verification["result"]
    claim.auto_checks = verification["checks"]
    claim.auto_reason = verification["reason"]
    claim.estimated_payout = verification["estimated_payout"]

    if verification["result"] == "auto_approve":
        claim.status = "auto_approved"
    elif verification["result"] == "auto_deny":
        claim.status = "auto_denied"
    else:
        claim.status = "under_review"

    db.add(claim)
    db.commit()

    return {
        "message": "Re-verification complete",
        "result":  verification["result"],
        "score":   verification["score"],
        "reason":  verification["reason"],
        "checks":  verification["checks"],
    }
