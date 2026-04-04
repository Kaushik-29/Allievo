"""
Plans API — GET /api/v1/plans
Manages the three-tier plan catalogue and worker enrollment.
"""
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.models.worker_plan import WorkerPlan
from app.models.weekly_premium import WeeklyPremium
from app.services.dynamic_premium_engine import (
    DynamicPremiumEngine,
    get_all_plans_with_premiums,
    PLAN_DEFS,
)

router = APIRouter(prefix="/plans", tags=["plans"])


# ─────────────────────────────────────────────────────────────────
# SCHEMAS
# ─────────────────────────────────────────────────────────────────

class EnrollRequest(BaseModel):
    worker_id: UUID
    plan_name: str


class UpgradeRequest(BaseModel):
    worker_id: UUID
    new_plan: str


# ─────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────

@router.get("")
def list_plans(
    lat: float = 17.4647,
    lon: float = 78.3513,
):
    """
    GET /api/v1/plans
    Returns all 3 plans with current computed premiums.
    The dynamic plan premium is computed live from OWM forecast.
    Lat/lon default to Kondapur, Hyderabad (Ravi's zone).
    """
    plans = get_all_plans_with_premiums(lat=lat, lon=lon)
    return {"plans": plans}


@router.post("/enroll")
def enroll_worker(
    body: EnrollRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    POST /api/v1/plans/enroll
    Enroll a worker in a plan. Creates a worker_plans row.
    Enforces 28-day waiting period before payout eligibility.
    """
    if body.plan_name not in PLAN_DEFS:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {body.plan_name}. Must be basic|dynamic|premium")

    # Cancel any existing active enrollment
    existing = (
        db.query(WorkerPlan)
        .filter(WorkerPlan.worker_id == body.worker_id, WorkerPlan.status == "active")
        .first()
    )
    if existing:
        existing.status = "cancelled"
        db.add(existing)

    # Compute weekly premium
    engine = DynamicPremiumEngine()
    if body.plan_name == "dynamic":
        result = engine.compute_dynamic_premium()
        weekly_premium = result["premium_amount"]
    else:
        weekly_premium = engine.get_static_premium(body.plan_name)

    now = datetime.utcnow()
    waiting_ends = now + timedelta(days=28)

    wp = WorkerPlan(
        worker_id=body.worker_id,
        plan_name=body.plan_name,
        enrolled_at=now,
        weekly_premium=weekly_premium,
        status="active",
        waiting_ends_at=waiting_ends,
        eligible_for_payout=False,
    )
    db.add(wp)
    db.commit()
    db.refresh(wp)

    return {
        "message": f"Successfully enrolled in {body.plan_name} plan",
        "enrollment": wp.to_dict(),
        "waiting_ends_at": waiting_ends.isoformat(),
        "note": "Payout eligibility begins after 28-day waiting period",
    }


@router.get("/worker/{worker_id}")
def get_worker_plan(
    worker_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    GET /api/v1/plans/worker/{worker_id}
    Returns the worker's current plan + premium + payout cap.
    For dynamic plan, also returns this week's risk breakdown.
    """
    enrollment = (
        db.query(WorkerPlan)
        .filter(WorkerPlan.worker_id == worker_id, WorkerPlan.status == "active")
        .order_by(WorkerPlan.enrolled_at.desc())
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail="No active plan enrollment found")

    plan_def = PLAN_DEFS[enrollment.plan_name]

    # Check waiting period
    if not enrollment.eligible_for_payout and enrollment.waiting_ends_at:
        if datetime.utcnow() >= enrollment.waiting_ends_at:
            enrollment.eligible_for_payout = True
            db.commit()

    result = {
        "enrollment": enrollment.to_dict(),
        "plan": {
            "name":          enrollment.plan_name,
            "covered_hours": plan_def["covered_hours"],
            "days_per_week": plan_def["days_per_week"],
            "hours_per_day": plan_def["hours_per_day"],
            "max_payout":    plan_def["max_payout"],
            "plan_value":    plan_def["plan_value"],
            "claim_mode":    "manual_or_auto" if enrollment.plan_name == "basic" else "auto_only",
        },
    }

    # For dynamic plan: include latest weekly premium record
    if enrollment.plan_name == "dynamic":
        latest = (
            db.query(WeeklyPremium)
            .filter(WeeklyPremium.worker_id == worker_id)
            .order_by(WeeklyPremium.computed_at.desc())
            .first()
        )
        if latest:
            result["this_week"] = latest.to_dict()

    return result


@router.post("/compute-dynamic")
def compute_dynamic_now(
    worker_id: UUID,
    lat: float = 17.4647,
    lon: float = 78.3513,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    POST /api/v1/plans/compute-dynamic?worker_id=...&lat=...&lon=...
    Admin/demo endpoint: manually trigger the Sunday premium computation for one worker.
    Stores result in weekly_premiums table.
    """
    engine = DynamicPremiumEngine()

    # Get last week multiplier for smoothing
    last = (
        db.query(WeeklyPremium)
        .filter(WeeklyPremium.worker_id == worker_id)
        .order_by(WeeklyPremium.computed_at.desc())
        .first()
    )
    last_mult = float(last.multiplier_applied) if (last and last.multiplier_applied) else 1.0

    result = engine.compute_dynamic_premium(lat=lat, lon=lon, last_week_multiplier=last_mult)

    # Next Monday
    today = datetime.utcnow().date()
    days_until_monday = (7 - today.weekday()) % 7 or 7
    week_start = today + timedelta(days=days_until_monday)

    record = WeeklyPremium(
        worker_id=worker_id,
        plan_name="dynamic",
        week_start=week_start,
        premium_amount=result["premium_amount"],
        week_risk_score=result["week_risk_score"],
        peak_rain_mm=result["peak_rain_mm"],
        peak_temp_c=result["peak_temp_c"],
        peak_aqi=result["peak_aqi"],
        multiplier_applied=result["multiplier_applied"],
        plain_reason=result["plain_reason"],
    )
    db.add(record)

    # Update the worker_plans weekly_premium
    enrollment = (
        db.query(WorkerPlan)
        .filter(WorkerPlan.worker_id == worker_id, WorkerPlan.plan_name == "dynamic", WorkerPlan.status == "active")
        .first()
    )
    if enrollment:
        enrollment.weekly_premium = result["premium_amount"]
        db.add(enrollment)

    db.commit()
    db.refresh(record)

    return {
        "message": "Dynamic premium computed and stored",
        "week_start": str(week_start),
        "result": result,
        "record_id": str(record.id),
    }


@router.post("/upgrade")
def upgrade_plan(
    body: UpgradeRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    POST /api/v1/plans/upgrade
    Switch plan (takes effect next Monday — technically re-enrolls immediately for demo).
    """
    if body.new_plan not in PLAN_DEFS:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {body.new_plan}")

    existing = (
        db.query(WorkerPlan)
        .filter(WorkerPlan.worker_id == body.worker_id, WorkerPlan.status == "active")
        .first()
    )
    if not existing:
        raise HTTPException(status_code=404, detail="No active plan to upgrade from")

    if existing.plan_name == body.new_plan:
        raise HTTPException(status_code=400, detail="Already on this plan")

    # For demo purposes: switch immediately (preserve wait period from original enrollment)
    engine = DynamicPremiumEngine()
    if body.new_plan == "dynamic":
        result = engine.compute_dynamic_premium()
        premium = result["premium_amount"]
    else:
        premium = engine.get_static_premium(body.new_plan)

    existing.plan_name = body.new_plan
    existing.weekly_premium = premium
    db.add(existing)
    db.commit()

    return {
        "message": f"Plan upgraded to {body.new_plan}",
        "new_weekly_premium": premium,
        "effective_from": "immediately (next Monday in production)",
    }


@router.get("/forecast-bars")
def get_forecast_bars(
    lat: float = 17.4647,
    lon: float = 78.3513,
):
    """
    GET /api/v1/plans/forecast-bars?lat=&lon=
    Lightweight call for the plan cards — returns rain/temp/AQI bars + multiplier.
    No auth needed (public data).
    """
    engine = DynamicPremiumEngine()
    bars = engine.get_forecast_risk_bars(lat=lat, lon=lon)
    return bars
