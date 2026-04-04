"""
Allievo Demo Seed Script — DEVTrails 2026
Idempotent: Run multiple times safely. Creates Ravi (demo persona) with full data.
Usage: python demo_seed.py
"""
import sys, os, random, math
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta, date
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.worker import Worker
from app.models.zone_score import ZoneScore
from app.models.policy import Policy
from app.models.earnings_snapshot import EarningsSnapshot
from app.models.device_fingerprint import DeviceFingerprint
from app.models.gps_ping import GpsPing
from app.models.trigger_event import TriggerEvent
from sqlalchemy import text

db = SessionLocal()

print("=" * 60)
print("  Allievo Demo Seed — DEVTrails 2026")
print("=" * 60)

# ── 1. ZONE (Kondapur, Hyderabad)
zone = db.query(ZoneScore).filter(ZoneScore.zone_name == "Kondapur").first()
if not zone:
    zone = ZoneScore(
        zone_name="Kondapur",
        city="Hyderabad",
        risk_multiplier=1.15,
        disruption_days_yr=42,
        seasonal_factor=1.4,
        zone_type="flood",
        risk_score_current=0.58,
        hist_risk=0.52,
        weather_risk=0.70,
        pollution_risk=0.25,
        traffic_risk=0.40,
        live_event_risk=0.30,
        last_scored_at=datetime.utcnow(),
    )
    # Set a simple polygon around Kondapur centroid (17.4600, 78.3650) — ~2km box
    try:
        db.execute(text("""
            UPDATE zone_scores SET zone_boundary = ST_SetSRID(ST_MakePolygon(ST_GeomFromText(
                'LINESTRING(78.355 17.450, 78.375 17.450, 78.375 17.470, 78.355 17.470, 78.355 17.450)'
            )), 4326) WHERE zone_name = 'Kondapur'
        """))
    except Exception:
        pass  # PostGIS might not be set; non-fatal
    db.add(zone)
    db.commit()
    db.refresh(zone)
    print(f"✅ Zone created: Kondapur (id={zone.id})")
else:
    print(f"✓  Zone exists: Kondapur (id={zone.id})")

# ── 2. WORKER (Ravi)
worker = db.query(Worker).filter(Worker.username == "ravi_kondapur").first()
if not worker:
    worker = Worker(
        username="ravi_kondapur",
        hashed_password=get_password_hash("Ravi@1234"),
        name="Ravi Kumar",
        phone="9876500001",
        email="ravi@allievo.demo",
        city="Hyderabad",
        aadhar_no="123456789012",
        pan_no="ABCPR1234F",
        primary_platform="zomato",
        work_location="Kondapur",
        current_location="Kondapur, Hyderabad",
        working_proof="Zomato delivery partner badge #ZOM-HYD-4521",
        upi_id="ravi.kumar@okaxis",
        is_active=True,
        onboarded_at=datetime.utcnow() - timedelta(days=120),
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)
    print(f"✅ Worker created: Ravi Kumar (id={worker.id})")
else:
    print(f"✓  Worker exists: Ravi Kumar (id={worker.id})")

# ── 3. DEVICE FINGERPRINT
fp = db.query(DeviceFingerprint).filter(DeviceFingerprint.worker_id == worker.id).first()
if not fp:
    fp = DeviceFingerprint(
        worker_id=worker.id,
        hardware_id_hash="demo-device-ravi-001",
        sim_carrier="Airtel",
        is_current=True,
        captured_at=datetime.utcnow(),
        session_type="onboarding",
    )
    db.add(fp)
    db.commit()
    print(f"✅ Device fingerprint registered")
else:
    print(f"✓  Device fingerprint exists")

# ── 4. EARNINGS SNAPSHOTS
for platform, dae, label in [("zomato", 820.0, "Zomato"), ("swiggy", 180.0, "Swiggy")]:
    snap = db.query(EarningsSnapshot).filter(
        EarningsSnapshot.worker_id == worker.id,
        EarningsSnapshot.platform == platform
    ).first()
    if not snap:
        snap = EarningsSnapshot(
            worker_id=worker.id,
            platform=platform,
            snapshot_date=date.today(),
            total_settlements=dae * 87,
            active_days_count=87,
            dae_single=dae,
            dae_confidence_adj=dae,
            raw_days_available=90,
        )
        db.add(snap)
        print(f"✅ Earnings snapshot: {label} DAE=₹{dae}/day")
    else:
        print(f"✓  Earnings snapshot exists: {label}")
db.commit()

# ── 5. POLICY (Standard tier, already past waiting period)
policy = db.query(Policy).filter(
    Policy.worker_id == worker.id,
    Policy.status == "active"
).first()
if not policy:
    week_start = date.today() - timedelta(days=28 + 7)  # Past 4-week waiting period
    policy = Policy(
        worker_id=worker.id,
        zone_id=zone.id,
        tier="standard",
        week_start=week_start,
        week_end=week_start + timedelta(days=6),
        premium_paid=68.50,
        static_base_premium=40.0,
        risk_score_at_issue=0.58,
        seasonal_factor=1.40,
        loyalty_weeks=6,
        loyalty_adjustment=0.95,
        status="active",
        max_weekly_payout=700.0,
        coverage_hours_day=6,
        coverage_factor=1.0,
        waiting_weeks_done=4,
        eligible_for_payout=True,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    print(f"✅ Policy created: Standard, eligible_for_payout=True (id={policy.id})")
else:
    # Ensure it's eligible
    policy.eligible_for_payout = True
    db.commit()
    print(f"✓  Policy exists: {policy.tier} (id={policy.id})")

# ── 6. GPS PINGS (90 days, Kondapur area, realistic road drift)
existing_pings = db.query(GpsPing).filter(GpsPing.worker_id == worker.id).count()
if existing_pings < 100:
    print("⏳ Generating 90 days GPS pings (this takes ~10s)...")
    rng = random.Random(42)
    # Kondapur centroid
    BASE_LAT, BASE_LNG = 17.4600, 78.3650
    now = datetime.utcnow()
    pings_added = 0

    for day_offset in range(90):
        ping_date = now - timedelta(days=90 - day_offset)
        # Ravi works 87 out of 90 days
        if day_offset in [15, 42, 67]:  # 3 rest days
            continue
        # 8 pings per working day (roughly every hour)
        work_start = ping_date.replace(hour=9, minute=0, second=0, microsecond=0)
        for ping_num in range(8):
            ping_time = work_start + timedelta(hours=ping_num, minutes=rng.randint(0, 45))
            # Road-following drift: ±0.002 degrees (~200m) with natural micro-jitter
            lat = BASE_LAT + rng.uniform(-0.008, 0.008) + rng.gauss(0, 0.00003)
            lng = BASE_LNG + rng.uniform(-0.008, 0.008) + rng.gauss(0, 0.00003)
            speed = rng.uniform(8.0, 32.0)  # delivery bike speed 8–32 km/h
            # Cell tower ~200m offset from GPS (realistic)
            tower_lat = lat + rng.gauss(0, 0.0018)
            tower_lng = lng + rng.gauss(0, 0.0018)
            tower_matches = True  # within 500m

            try:
                ping = GpsPing(
                    worker_id=worker.id,
                    location=f"SRID=4326;POINT({lng} {lat})",
                    accuracy_meters=rng.uniform(3, 15),
                    speed_kmh=speed,
                    cell_tower_lat=tower_lat,
                    cell_tower_lng=tower_lng,
                    cell_tower_matches=tower_matches,
                    pinged_at=ping_time,
                    session_id=f"session-ravi-{day_offset}",
                )
                db.add(ping)
                pings_added += 1
            except Exception as e:
                pass

    db.commit()
    print(f"✅ GPS pings created: {pings_added} pings over 87 work days")
else:
    print(f"✓  GPS pings exist: {existing_pings} pings")

print()
print("=" * 60)
print("  SEED COMPLETE!")
print(f"  Username : ravi_kondapur")
print(f"  Password : Ravi@1234")
print(f"  UPI      : ravi.kumar@okaxis")
print(f"  Zone     : Kondapur, Hyderabad")
print(f"  DAE      : ₹1,000/day (₹820 Zomato + ₹180 Swiggy)")
print("=" * 60)

db.close()
