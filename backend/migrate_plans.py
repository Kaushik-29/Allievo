"""
migrate_plans.py
================
Run this once to:
  1. Create the new tables: plans, worker_plans, weekly_premiums
  2. Seed the 3 plan definitions
  3. Enroll the demo worker (Ravi) in the dynamic plan

Usage:
  cd d:\test1-main\backend
  .venv\Scripts\python.exe migrate_plans.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta
from sqlalchemy import text

# Bootstrap app settings
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal

# Import all models so SQLAlchemy knows them
import app.models  # noqa: F401

from app.models.plan import Plan
from app.models.worker_plan import WorkerPlan
from app.models.weekly_premium import WeeklyPremium
from app.models.worker import Worker

HOURLY_RATE = 80.0  # ₹/hr

PLAN_SEED = [
    {
        "name":          "basic",
        "days_per_week": 2,
        "hours_per_day": 2,
        "covered_hours": 4,
        "premium_rate":  0.15,
        "plan_value":    HOURLY_RATE * 4,      # ₹320
        "max_payout":    HOURLY_RATE * 4,
        "claim_mode":    "manual_or_auto",
        "description":   "Covers 2 days × 2 hrs/day. Worker manually selects claim window.",
    },
    {
        "name":          "dynamic",
        "days_per_week": 3,
        "hours_per_day": 4,
        "covered_hours": 12,
        "premium_rate":  None,                 # computed each Sunday
        "plan_value":    HOURLY_RATE * 12,     # ₹960
        "max_payout":    HOURLY_RATE * 12,
        "claim_mode":    "auto_only",
        "description":   "Covers 3 days × 4 hrs/day. Premium adjusts weekly via weather forecast.",
    },
    {
        "name":          "premium",
        "days_per_week": 4,
        "hours_per_day": 6,
        "covered_hours": 24,
        "premium_rate":  0.30,
        "plan_value":    HOURLY_RATE * 24,     # ₹1,920
        "max_payout":    HOURLY_RATE * 24,
        "claim_mode":    "auto_only",
        "description":   "Covers 4 days × 6 hrs/day. Maximum protection, priority review.",
    },
]


def run():
    print("=" * 60)
    print("Allievo — Plan System Migration")
    print("=" * 60)

    # 1. Create tables
    print("\n[1] Creating new tables (plans, worker_plans, weekly_premiums)...")
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("    ✓ Tables created (or already exist)")
    except Exception as e:
        print(f"    ✗ Error creating tables: {e}")
        sys.exit(1)

    db = SessionLocal()
    try:
        # 2. Seed plan catalogue
        print("\n[2] Seeding plan catalogue...")
        for seed in PLAN_SEED:
            existing = db.query(Plan).filter(Plan.name == seed["name"]).first()
            if existing:
                # Update the existing plan definition
                for k, v in seed.items():
                    setattr(existing, k, v)
                db.add(existing)
                print(f"    ↺ Updated plan: {seed['name']}")
            else:
                plan = Plan(**seed)
                db.add(plan)
                print(f"    + Inserted plan: {seed['name']}")
        db.commit()

        # Print plan summary
        print("\n    Plan Catalogue:")
        print(f"    {'Plan':10} {'Covered Hrs':12} {'Plan Value':12} {'Weekly Premium':15} {'Max Payout':12}")
        print(f"    {'-'*62}")
        for seed in PLAN_SEED:
            if seed["premium_rate"]:
                wp = seed["plan_value"] * seed["premium_rate"]
                wp_str = f"₹{wp:.0f} (fixed)"
            else:
                wp_str = "Dynamic (weather)"
            print(f"    {seed['name']:10} {seed['covered_hours']:<12} ₹{seed['plan_value']:<11.0f} {wp_str:<15} ₹{seed['max_payout']:<12.0f}")

        # 3. Enroll demo worker
        print("\n[3] Enrolling demo worker (Ravi Kumar) in dynamic plan...")
        ravi = db.query(Worker).filter(Worker.username == "ravi_kondapur").first()
        if not ravi:
            print("    ⚠ Demo worker 'ravi_kondapur' not found — skipping enrollment.")
            print("      Run demo_seed.py first, then re-run this script.")
        else:
            # Cancel existing plan
            existing_enrollment = (
                db.query(WorkerPlan)
                .filter(WorkerPlan.worker_id == ravi.id, WorkerPlan.status == "active")
                .first()
            )
            if existing_enrollment:
                existing_enrollment.status = "cancelled"
                print(f"    ↺ Cancelled existing '{existing_enrollment.plan_name}' enrollment")

            # Dynamic plan premium: ₹48 × 1.35 = ₹64.8 (moderate-risk mock)
            dynamic_premium = round(48.0 * 1.35, 2)  # ₹64.80

            now = datetime.utcnow()
            enrollment = WorkerPlan(
                worker_id=ravi.id,
                plan_name="dynamic",
                enrolled_at=now - timedelta(days=30),  # already past waiting period
                weekly_premium=dynamic_premium,
                status="active",
                waiting_ends_at=now - timedelta(days=2),  # already eligible
                eligible_for_payout=True,
            )
            db.add(enrollment)
            db.commit()
            print(f"    ✓ Ravi enrolled in Dynamic plan | Weekly premium: ₹{dynamic_premium}")

            # Seed a sample weekly_premiums record for demo
            from datetime import date
            today = date.today()
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)

            existing_wp = (
                db.query(WeeklyPremium)
                .filter(
                    WeeklyPremium.worker_id == ravi.id,
                    WeeklyPremium.week_start == week_start
                )
                .first()
            )
            if not existing_wp:
                wp_record = WeeklyPremium(
                    worker_id=ravi.id,
                    plan_name="dynamic",
                    week_start=week_start,
                    premium_amount=dynamic_premium,
                    week_risk_score=0.32,
                    peak_rain_mm=28.0,
                    peak_temp_c=36.0,
                    peak_aqi=142.0,
                    multiplier_applied=1.35,
                    plain_reason="Normal week — standard rate applied. (demo seed)",
                )
                db.add(wp_record)
                db.commit()
                print(f"    ✓ Seeded weekly_premiums record for week of {week_start}")

        print("\n" + "=" * 60)
        print("Migration complete! Restart the backend to apply changes.")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\n✗ Migration failed: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run()
