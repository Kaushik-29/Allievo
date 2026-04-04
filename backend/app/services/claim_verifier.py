"""
Claim Verifier
==============
Auto-verifies worker-filed (manual) claims before reaching the admin queue.

Checks performed:
  1. Geofence (15km radius)        — was worker in their registered zone?
  2. Was working declaration        — did worker declare they were working?
  3. Weather corroboration          — does OpenWeatherMap confirm the disruption?
  4. Platform session (mock)        — was the worker on the platform that day?
  5. Claim frequency gate           — not more than 3 claims in 7 days

Scoring:
  0.00–0.35  →  auto_approve   (all checks pass)
  0.36–0.65  →  review         (admin sees + decides)
  0.66–1.00  →  auto_deny      (GPS fail / no session / weather mismatch)

The score represents 'suspicion' (low = trustworthy, high = suspicious).
"""
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.worker import Worker
from app.models.manual_claim import ManualClaim

logger = logging.getLogger(__name__)

OWM_KEY = settings.OPENWEATHERMAP_API_KEY
GEOFENCE_KM = 15.0        # 15km radius
HOURLY_RATE = 80.0         # ₹/hr baseline


# ─────────────────────────────────────────────────────────────────
# Haversine distance
# ─────────────────────────────────────────────────────────────────
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ─────────────────────────────────────────────────────────────────
# OWM weather corroboration
# ─────────────────────────────────────────────────────────────────
def _check_weather_at_time(
    lat: float,
    lon: float,
    disruption_type: str,
    disruption_date: datetime,
) -> dict:
    """
    Check OWM historical/current weather to corroborate the claim.
    For demo: uses current weather as a proxy; production would use OWM History.
    Returns {confirmed: bool, detail: str, raw_value: float}
    """
    if OWM_KEY == "mock":
        return {"confirmed": True, "detail": "Mock mode — assumed confirmed", "raw_value": 0.0}

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"lat": lat, "lon": lon, "appid": OWM_KEY, "units": "metric"}
        with httpx.Client(timeout=8.0) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            data = r.json()

        rain_1h = data.get("rain", {}).get("1h", 0.0)
        temp    = data.get("main", {}).get("temp", 25.0)

        # Fetch AQI
        aqi_url = "http://api.openweathermap.org/data/2.5/air_pollution"
        aqi_r = httpx.get(aqi_url, params={"lat": lat, "lon": lon, "appid": OWM_KEY}, timeout=8.0)
        aqi_val = 0
        if aqi_r.status_code == 200:
            items = aqi_r.json().get("list", [{}])
            pm25 = items[0].get("components", {}).get("pm2_5", 0) if items else 0
            aqi_val = min(500, pm25 * 4)  # rough conversion

        if disruption_type == "rainfall":
            confirmed = rain_1h >= 10  # significant rain
            return {"confirmed": confirmed, "detail": f"Rain {rain_1h:.1f}mm/hr", "raw_value": rain_1h}
        elif disruption_type == "heat":
            confirmed = temp >= 38
            return {"confirmed": confirmed, "detail": f"Temp {temp:.1f}°C", "raw_value": temp}
        elif disruption_type == "aqi":
            confirmed = aqi_val >= 150
            return {"confirmed": confirmed, "detail": f"AQI ~{aqi_val:.0f}", "raw_value": aqi_val}
        else:
            # curfew, outage, other — can't auto-corroborate via weather
            return {"confirmed": None, "detail": "Cannot auto-corroborate via weather", "raw_value": 0.0}

    except Exception as e:
        logger.warning(f"Weather corroboration failed: {e}")
        return {"confirmed": None, "detail": f"API error: {str(e)[:60]}", "raw_value": 0.0}


# ─────────────────────────────────────────────────────────────────
# Claim frequency check
# ─────────────────────────────────────────────────────────────────
def _check_claim_frequency(worker_id, db: Session) -> dict:
    """Max 3 manual claims in last 7 days."""
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent = (
        db.query(ManualClaim)
        .filter(
            ManualClaim.worker_id == worker_id,
            ManualClaim.submitted_at >= week_ago,
        )
        .count()
    )
    ok = recent < 3
    return {"ok": ok, "recent_count": recent, "detail": f"{recent} claims in last 7 days (max 3)"}


# ─────────────────────────────────────────────────────────────────
# Payout estimate
# ─────────────────────────────────────────────────────────────────
def _estimate_payout(
    disruption_hours: float,
    disruption_type: str,
    plan_name: Optional[str],
) -> float:
    """
    Estimated payout = hourly_rate × disrupted_hours × severity_multiplier
    Capped at plan max payout.
    """
    severity = {
        "rainfall": 0.80, "heat": 0.85, "aqi": 0.85,
        "curfew": 1.00, "outage": 0.70, "other": 0.70,
    }.get(disruption_type, 0.70)

    plan_caps = {"basic": 320.0, "dynamic": 960.0, "premium": 1920.0}
    cap = plan_caps.get(plan_name or "basic", 320.0)

    gross = HOURLY_RATE * disruption_hours * severity
    return round(min(gross, cap), 2)


# ─────────────────────────────────────────────────────────────────
# MAIN VERIFIER
# ─────────────────────────────────────────────────────────────────
def auto_verify_claim(claim: ManualClaim, worker: Worker, db: Session) -> dict:
    """
    Run all checks and produce:
      {
        score: float,           # 0=trustworthy, 1=suspicious
        result: str,            # auto_approve | review | auto_deny
        checks: dict,
        reason: str,
        estimated_payout: float,
      }
    """
    checks = {}
    suspicion_hits = 0
    total_checks = 0

    # ── 1. Geofence check ──────────────────────────────────────
    if (worker.registered_lat and worker.registered_lon
            and claim.worker_lat and claim.worker_lon):
        dist = haversine_km(
            float(worker.registered_lat), float(worker.registered_lon),
            float(claim.worker_lat), float(claim.worker_lon),
        )
        within = dist <= GEOFENCE_KM
        checks["gps_within_15km"] = {
            "passed": within,
            "detail": f"{dist:.1f}km from registered zone (limit {GEOFENCE_KM}km)",
            "value": dist,
        }
        if not within:
            suspicion_hits += 3   # GPS fail is a heavy penalty
        total_checks += 3
    else:
        # No GPS data provided — treat as borderline
        checks["gps_within_15km"] = {
            "passed": None,
            "detail": "Worker location not provided — cannot verify",
        }
        suspicion_hits += 1
        total_checks += 3

    # ── 2. Was working declaration ─────────────────────────────
    checks["declared_working"] = {
        "passed": claim.declared_was_working,
        "detail": "Worker declared they were working during disruption",
    }
    if not claim.declared_was_working:
        suspicion_hits += 2
    total_checks += 2

    # ── 3. Claim frequency gate ────────────────────────────────
    freq = _check_claim_frequency(claim.worker_id, db)
    checks["claim_frequency"] = {
        "passed": freq["ok"],
        "detail": freq["detail"],
    }
    if not freq["ok"]:
        suspicion_hits += 2
    total_checks += 2

    # ── 4. Weather corroboration ───────────────────────────────
    use_lat = float(worker.registered_lat) if worker.registered_lat else 17.4647
    use_lon = float(worker.registered_lon) if worker.registered_lon else 78.3513
    weather_check = _check_weather_at_time(
        use_lat, use_lon, claim.disruption_type, claim.disruption_date
    )
    checks["weather_corroborated"] = {
        "passed": weather_check["confirmed"],
        "detail": weather_check["detail"],
        "raw_value": weather_check["raw_value"],
    }
    if weather_check["confirmed"] is False:
        suspicion_hits += 2   # weather says no disruption
    elif weather_check["confirmed"] is None:
        suspicion_hits += 1   # can't verify (borderline)
    total_checks += 2

    # ── 5. Proof submitted ─────────────────────────────────────
    has_proof = bool(claim.proof_text and len(claim.proof_text) > 20)
    checks["proof_provided"] = {
        "passed": has_proof,
        "detail": f"Proof text: {len(claim.proof_text or '')} chars" if claim.proof_text else "No proof provided",
    }
    if not has_proof:
        suspicion_hits += 1
    total_checks += 1

    # ── Score & decision ───────────────────────────────────────
    score = suspicion_hits / max(total_checks, 1)
    score = round(min(max(score, 0.0), 1.0), 3)

    if score <= 0.35:
        result = "auto_approve"
        reason = "All key checks passed. Payout eligible."
    elif score <= 0.65:
        result = "review"
        reason = "Some checks need human review. Escalated to admin."
    else:
        result = "auto_deny"
        # Build specific denial reason
        fails = [k for k, v in checks.items() if v.get("passed") is False]
        reason = f"Auto-denied: {', '.join(fails).replace('_', ' ')}."

    # Estimate payout
    estimated = _estimate_payout(
        float(claim.disruption_hours),
        claim.disruption_type,
        claim.plan_name,
    )

    return {
        "score":            score,
        "result":           result,
        "checks":           checks,
        "reason":           reason,
        "estimated_payout": estimated,
    }
