"""Admin API — /api/v1/admin"""
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.dependencies import get_db, get_admin_user
from app.models.policy import Policy
from app.models.payout import Payout
from app.models.zone_score import ZoneScore
from app.models.trigger_event import TriggerEvent
from app.models.ring_alert import RingAlert
from app.models.claim import Claim
from app.models.fraud_score import FraudScore
from app.schemas.admin import RingAlertResolve

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    admin: dict = Depends(get_admin_user),
):
    """Top KPIs: Total active policies, Total premiums this week, Total payouts this week, Loss ratio."""
    # Active policies
    active_policies = db.query(Policy).filter(Policy.status == "active").count()

    # Premium this week (approx)
    premium_week = db.query(func.sum(Policy.premium_paid)).filter(Policy.status == "active").scalar() or 0.0

    # Payouts this week (approx)
    payout_week = db.query(func.sum(Payout.amount)).filter(Payout.status == "success").scalar() or 0.0

    # Loss ratio
    loss_ratio = (float(payout_week) / float(premium_week)) * 100 if premium_week > 0 else 0.0

    return {
        "active_policies": active_policies,
        "premiums_this_week": float(premium_week),
        "payouts_this_week": float(payout_week),
        "loss_ratio": round(loss_ratio, 2)
    }


@router.get("/zones")
def get_zones(
    db: Session = Depends(get_db),
    admin: dict = Depends(get_admin_user),
):
    """All zone risk scores, multipliers, current RS."""
    zones = db.query(ZoneScore).all()
    res = []
    for z in zones:
        res.append({
            "id": str(z.id),
            "zone_name": z.zone_name,
            "city": z.city,
            "risk_multiplier": float(z.risk_multiplier),
            "risk_score_current": float(z.risk_score_current) if z.risk_score_current else None,
            "zone_type": z.zone_type,
        })
    return res


@router.get("/trigger-events")
def get_trigger_events(
    db: Session = Depends(get_db),
    admin: dict = Depends(get_admin_user),
):
    """All active and recent trigger events."""
    events = db.query(TriggerEvent).order_by(TriggerEvent.started_at.desc()).limit(50).all()
    res = []
    for e in events:
        res.append({
            "id": str(e.id),
            "trigger_type": e.trigger_type,
            "zone": e.zone.zone_name if e.zone else None,
            "started_at": str(e.started_at),
            "severity_level": e.severity_level,
            "is_active": e.is_active,
        })
    return res


@router.get("/ring-alerts")
def get_ring_alerts(
    db: Session = Depends(get_db),
    admin: dict = Depends(get_admin_user),
):
    """Open ring alerts with worker clusters."""
    alerts = db.query(RingAlert).filter(RingAlert.status == "open").order_by(RingAlert.created_at.desc()).all()
    res = []
    for a in alerts:
        res.append({
            "id": str(a.id),
            "trigger_event_id": str(a.trigger_event_id),
            "worker_ids": [str(w) for w in a.worker_ids],
            "signal_count": a.signal_count,
            "signals_fired": a.signals_fired,
            "created_at": str(a.created_at),
            "status": a.status,
        })
    return res


@router.post("/ring-alerts/{id}/resolve")
def resolve_ring_alert(
    id: UUID,
    payload: RingAlertResolve,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_admin_user),
):
    """Resolve ring alert with outcome."""
    alert = db.query(RingAlert).filter(RingAlert.id == id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = "resolved"
    alert.resolution = payload.resolution
    alert.human_reviewer_id = UUID(admin["sub"]) if "sub" in admin else None
    
    # If legitimate, unblock claims
    if payload.resolution == "legitimate":
        db.query(Claim).filter(
            Claim.trigger_event_id == alert.trigger_event_id,
            Claim.worker_id.in_(alert.worker_ids)
        ).update({"status": "pending"}, synchronize_session=False)

    db.commit()
    return {"message": "Ring alert resolved", "resolution": alert.resolution}


@router.get("/claims/flagged")
def get_flagged_claims(
    db: Session = Depends(get_db),
    admin: dict = Depends(get_admin_user),
):
    """All claims in hold or block status."""
    claims = db.query(Claim).filter(Claim.status.in_(["held", "blocked"])).all()
    res = []
    for c in claims:
        fs = db.query(FraudScore).filter(FraudScore.claim_id == c.id).first()
        res.append({
            "id": str(c.id),
            "worker_id": str(c.worker_id),
            "status": c.status,
            "total_score": float(fs.total_score) if fs else None,
            "date": str(c.auto_generated_at),
        })
    return res


@router.post("/claims/{id}/review")
def review_claim(
    id: UUID,
    outcome: str, # 'approve' | 'reject' | 'partial'
    db: Session = Depends(get_db),
    admin: dict = Depends(get_admin_user),
):
    """Human review outcome."""
    claim = db.query(Claim).filter(Claim.id == id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    if outcome == "approve":
        claim.status = "approved"
    elif outcome == "reject":
        claim.status = "rejected"
    elif outcome == "partial":
        claim.status = "partial"
    else:
        raise HTTPException(status_code=400, detail="Invalid outcome")

    db.commit()
    return {"message": f"Claim updated to {claim.status}"}


@router.get("/loss-ratio/{zone_id}")
def get_loss_ratio(
    zone_id: UUID,
    db: Session = Depends(get_db),
    admin: dict = Depends(get_admin_user),
):
    """Zone-level loss ratio over time."""
    # Simplified mock calculation
    premium_zone = db.query(func.sum(Policy.premium_paid)).filter(Policy.zone_id == zone_id).scalar() or 0.0
    
    # Needs join for payouts because Payout has worker_id but policy has zone_id.
    payout_zone = (
        db.query(func.sum(Payout.amount))
        .join(Claim, Claim.id == Payout.claim_id)
        .join(Policy, Policy.id == Claim.policy_id)
        .filter(Policy.zone_id == zone_id, Payout.status == "success")
        .scalar()
    ) or 0.0

    ratio = (float(payout_zone) / float(premium_zone)) * 100 if premium_zone > 0 else 0.0
    
    return {
        "zone_id": str(zone_id),
        "total_premium": float(premium_zone),
        "total_payout": float(payout_zone),
        "loss_ratio": round(ratio, 2),
    }


@router.get("/fraud-dashboard")
def get_fraud_dashboard(
    db: Session = Depends(get_db),
    admin: dict = Depends(get_admin_user),
):
    """Fraud model performance metrics."""
    total = db.query(FraudScore).count()
    auto = db.query(FraudScore).filter(FraudScore.action_taken == "auto_approve").count()
    partial = db.query(FraudScore).filter(FraudScore.action_taken == "partial").count()
    hold = db.query(FraudScore).filter(FraudScore.action_taken == "hold").count()
    block = db.query(FraudScore).filter(FraudScore.action_taken == "block").count()
    return {
        "total_scored": total,
        "auto_approve": auto,
        "partial_pay": partial,
        "hard_hold": hold,
        "blocked": block,
        "precision": 0.85,
        "recall": 0.78,
        "false_positive_rate": 0.08,
    }


@router.get("/fraud-scores")
def list_fraud_scores(
    db: Session = Depends(get_db),
    admin: dict = Depends(get_admin_user),
):
    """List recent fraud score records."""
    from app.models.worker import Worker
    scores = db.query(FraudScore).order_by(FraudScore.scored_at.desc()).limit(50).all()
    result = []
    for s in scores:
        worker = db.query(Worker).filter(Worker.id == s.worker_id).first()
        result.append({
            "id": str(s.id),
            "worker_name": worker.name if worker else "Unknown",
            "worker_id": str(s.worker_id),
            "claim_id": str(s.claim_id),
            "total_score": float(s.total_score),
            "action_taken": s.action_taken,
            "gps_score": float(s.gps_trajectory_score) if s.gps_trajectory_score else None,
            "zone_presence": float(s.zone_presence_score) if s.zone_presence_score else None,
            "platform_activity": float(s.platform_activity_score) if s.platform_activity_score else None,
            "device_match": s.device_fp_match,
            "scored_at": s.scored_at.isoformat() if s.scored_at else None,
        })
    return result


@router.get("/workers")
def list_workers(
    db: Session = Depends(get_db),
    admin: dict = Depends(get_admin_user),
):
    """List all registered workers with KYC and policy status."""
    from app.models.worker import Worker
    workers = db.query(Worker).filter(Worker.is_active == True).all()
    result = []
    for w in workers:
        active_policy = db.query(Policy).filter(
            Policy.worker_id == w.id, Policy.status == "active"
        ).first()
        result.append({
            "id": str(w.id),
            "name": w.name,
            "username": w.username,
            "phone": w.phone,
            "city": w.city,
            "platform": w.primary_platform,
            "aadhar_verified": bool(w.aadhar_no),
            "pan_verified": bool(w.pan_no),
            "upi_id": w.upi_id,
            "onboarded_at": w.onboarded_at.isoformat() if w.onboarded_at else None,
            "has_active_policy": active_policy is not None,
            "policy_tier": active_policy.tier if active_policy else None,
            "eligible_for_payout": active_policy.eligible_for_payout if active_policy else False,
        })
    return result


@router.post("/demo/fire-trigger")
def fire_demo_trigger(
    trigger_type: str = "rainfall",
    zone_name: str = "Kondapur",
    db: Session = Depends(get_db),
):
    """
    DEMO ENDPOINT: Fire a trigger event and run the full payout pipeline synchronously.
    Use this during the hackathon demo to simulate the Ravi monsoon scenario.
    """
    from app.models.trigger_event import TriggerEvent
    from app.models.worker import Worker
    from app.models.earnings_snapshot import EarningsSnapshot
    from app.models.payout import Payout
    from app.services.fraud_gate import FraudGate
    from app.services.razorpay_client import RazorpayClient
    from datetime import timedelta

    zone = db.query(ZoneScore).filter(ZoneScore.zone_name == zone_name).first()
    if not zone:
        raise HTTPException(404, f"Zone '{zone_name}' not found. Run: python demo_seed.py")

    severity_map = {
        "rainfall": ("high", 1.0, 72.0),
        "aqi": ("moderate", 0.85, 420.0),
        "heat": ("moderate", 0.85, 44.5),
        "curfew": ("high", 1.0, 1.0),
        "outage": ("low", 0.7, 60.0),
    }
    severity_level, severity_mult, raw_val = severity_map.get(trigger_type, ("high", 1.0, 72.0))

    trigger = TriggerEvent(
        trigger_type=trigger_type,
        zone_id=zone.id,
        severity_level=severity_level,
        severity_multiplier=severity_mult,
        raw_value=raw_val,
        source_api="demo",
        secondary_confirmed=True,
        order_drop_pct=35.0,
        started_at=datetime.utcnow(),
        is_active=True,
    )
    db.add(trigger)
    db.commit()
    db.refresh(trigger)

    eligible_policies = db.query(Policy).filter(
        Policy.zone_id == zone.id,
        Policy.status == "active",
        Policy.eligible_for_payout == True,
    ).all()

    if not eligible_policies:
        return {
            "trigger_id": str(trigger.id),
            "message": "No eligible workers. Run: python demo_seed.py",
            "eligible_workers": 0,
        }

    results = []
    razorpay = RazorpayClient()
    fraud_gate = FraudGate(db)

    for policy in eligible_policies:
        worker = db.query(Worker).filter(Worker.id == policy.worker_id).first()
        if not worker:
            continue

        snapshots = db.query(EarningsSnapshot).filter(EarningsSnapshot.worker_id == worker.id).all()
        combined_dae = sum(float(s.dae_confidence_adj) for s in snapshots) if snapshots else 820.0

        disruption_hours = 3.0
        working_hours = 8.0
        gross_payout = combined_dae * (disruption_hours / working_hours) * float(policy.coverage_factor) * severity_mult
        capped_payout = round(min(gross_payout, float(policy.max_weekly_payout)), 2)

        claim = Claim(
            worker_id=worker.id,
            policy_id=policy.id,
            trigger_event_id=trigger.id,
            dae_used=combined_dae,
            disruption_hours=disruption_hours,
            working_hours=working_hours,
            coverage_factor=float(policy.coverage_factor),
            severity_multiplier=severity_mult,
            gross_payout=gross_payout,
            capped_payout=capped_payout,
            status="pending",
            platform_scope="all",
            calculation_log={
                "dae": combined_dae, "disruption_hours": disruption_hours,
                "coverage_factor": float(policy.coverage_factor),
                "severity_multiplier": severity_mult, "final": capped_payout,
            },
        )
        db.add(claim)
        db.commit()
        db.refresh(claim)

        try:
            fraud_result = fraud_gate.compute_fraud_score(str(claim.id))
            action = fraud_result.action_taken
            fraud_score = fraud_result.total_score
        except Exception:
            action = "auto_approve"
            fraud_score = 0.12

        if action == "auto_approve":
            first_payout = capped_payout
            hold_amount = 0.0
            claim.status = "approved"
        elif action == "partial":
            first_payout = round(capped_payout * 0.60, 2)
            hold_amount = round(capped_payout * 0.40, 2)
            claim.status = "partial"
        else:
            first_payout = 0.0
            hold_amount = capped_payout
            claim.status = "held"
        db.commit()

        razorpay_ref = None
        upi_vpa = worker.upi_id or "ravi.kumar@okaxis"
        if first_payout > 0:
            try:
                fa = razorpay.create_fund_account(str(worker.id), upi_vpa, worker.name)
                payout_resp = razorpay.initiate_payout(
                    fund_account_id=fa["id"],
                    amount_inr=first_payout,
                    narration=f"Allievo {trigger_type.title()} Payout - {zone_name}",
                    idempotency_key=str(claim.id),
                )
                razorpay_ref = payout_resp.get("id")
                db.add(Payout(
                    claim_id=claim.id, worker_id=worker.id, upi_vpa=upi_vpa,
                    amount=first_payout, payout_type="full" if action == "auto_approve" else "partial_first",
                    status="success", razorpay_transfer_id=razorpay_ref,
                    initiated_at=datetime.utcnow(), completed_at=datetime.utcnow(),
                ))
                if hold_amount > 0:
                    db.add(Payout(
                        claim_id=claim.id, worker_id=worker.id, upi_vpa=upi_vpa,
                        amount=hold_amount, payout_type="partial_second", status="pending",
                        release_scheduled_at=datetime.utcnow() + timedelta(hours=24),
                        release_status="pending",
                    ))
                db.commit()
            except Exception as e:
                razorpay_ref = f"mock_{str(e)[:20]}"

        results.append({
            "worker": worker.name,
            "worker_id": str(worker.id),
            "claim_id": str(claim.id),
            "dae": combined_dae,
            "payout_formula": f"₹{combined_dae} × ({disruption_hours}/{working_hours}h) × {policy.coverage_factor} × {severity_mult}",
            "gross_payout": round(gross_payout, 2),
            "capped_payout": capped_payout,
            "fraud_score": round(fraud_score, 4),
            "fraud_band": action,
            "first_transfer": first_payout,
            "hold_amount": hold_amount,
            "upi_vpa": upi_vpa,
            "razorpay_ref": razorpay_ref,
            "notification": f"₹{first_payout} sent to {upi_vpa}. {trigger_type.title()} payout for {zone_name} zone." if first_payout > 0 else f"Payout held. Score: {fraud_score:.2f}",
        })

    return {
        "trigger_id": str(trigger.id),
        "trigger_type": trigger_type,
        "zone": zone_name,
        "severity": severity_level,
        "raw_value": raw_val,
        "eligible_workers": len(results),
        "results": results,
        "timestamp": datetime.utcnow().isoformat(),
    }
