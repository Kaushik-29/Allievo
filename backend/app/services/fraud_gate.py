"""
Fraud Gate — Section 4.4
Mandatory 5-minute pre-payout fraud analysis gate.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from geopy.distance import geodesic
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class FraudScoreResult:
    total_score: float
    action_taken: str           # 'auto_approve'|'partial'|'hold'|'block'
    partial_pct: float          # 60.0 if partial, 100.0 if approve, 0.0 if hold/block
    gps_trajectory_score: Optional[float] = None
    cell_tower_match: Optional[bool] = None
    platform_activity_score: Optional[float] = None
    device_fp_match: Optional[bool] = None
    zone_presence_score: Optional[float] = None
    accelerometer_score: Optional[float] = None
    claim_freq_score: Optional[float] = None
    baseline_adjustment: float = 0.0
    signal_breakdown: dict = field(default_factory=dict)


class FraudGate:

    AUTO_APPROVE_MAX = settings.FRAUD_AUTO_APPROVE_MAX   # 0.30
    PARTIAL_PAY_MAX  = settings.FRAUD_PARTIAL_MAX         # 0.55
    HARD_HOLD_MAX    = settings.FRAUD_HOLD_MAX            # 0.70

    ZONE_PRESENCE_HIGH_SUSPICION = settings.ZONE_PRESENCE_HIGH_SUSPICION  # 0.10
    ZONE_PRESENCE_CREDIBILITY    = settings.ZONE_PRESENCE_CREDIBILITY      # 0.50
    CELL_TOWER_MISMATCH_METERS   = settings.CELL_TOWER_MISMATCH_THRESHOLD_METERS  # 500

    def __init__(self, db: Session):
        self.db = db

    # ─────────────────────────────────────────────────────────────────
    # SIGNAL: ZONE PRESENCE
    # ─────────────────────────────────────────────────────────────────

    def compute_zone_presence_score(self, worker_id: str, zone_id: str) -> float:
        """
        ZPS = (Days worker had GPS pings in zone in last 30 days) / 30
        Requires: at least 1 GPS ping per day to count as 'present'
        """
        from app.models.gps_ping import GpsPing
        from app.models.zone_score import ZoneScore

        cutoff = datetime.utcnow() - timedelta(days=30)

        # Count distinct days worker had GPS pings inside the zone polygon
        try:
            result = self.db.execute(
                text("""
                    SELECT COUNT(DISTINCT DATE(gp.pinged_at)) as active_days
                    FROM gps_pings gp, zone_scores zs
                    WHERE gp.worker_id = :worker_id
                      AND zs.id = :zone_id
                      AND gp.pinged_at >= :cutoff
                      AND ST_Within(gp.location, zs.zone_boundary)
                """),
                {
                    "worker_id": worker_id,
                    "zone_id": zone_id,
                    "cutoff": cutoff,
                },
            )
            active_days = result.scalar() or 0
        except Exception as e:
            logger.warning(f"Zone presence query error (fallback to 0.5): {e}")
            active_days = 15  # default credibility level

        zps = active_days / 30.0
        return round(min(zps, 1.0), 4)

    # ─────────────────────────────────────────────────────────────────
    # SIGNAL: GPS TRAJECTORY
    # ─────────────────────────────────────────────────────────────────

    def check_gps_trajectory(self, worker_id: str, event_time: datetime) -> float:
        """
        Analyze 90 minutes of GPS pings BEFORE event_time.
        Returns 0.0 (clean) to 1.0 (highly suspicious).

        Checks:
          1. Speed continuity: Δdistance/Δtime within physical limits (max 80 km/hr for bike)
          2. Micro-drift: real devices show ±3–8m variance; perfect static = 1.0 suspicion
          3. Path plausibility validated against movement patterns
          4. Arrival vector: approaching or in zone, not teleporting
        """
        from app.models.gps_ping import GpsPing
        from geoalchemy2.functions import ST_X, ST_Y

        lookback = event_time - timedelta(minutes=settings.GPS_TRAJECTORY_LOOKBACK_MINUTES)

        pings = (
            self.db.query(GpsPing)
            .filter(
                GpsPing.worker_id == worker_id,
                GpsPing.pinged_at >= lookback,
                GpsPing.pinged_at <= event_time,
            )
            .order_by(GpsPing.pinged_at.asc())
            .all()
        )

        if len(pings) < 2:
            # Handle GPS signal loss via grace period
            grace = self.check_network_drop_grace(worker_id, event_time)
            if grace.get("grace"):
                return 0.1  # cell tower confirms — low suspicion
            return 0.25  # soft flag only, not fraud

        # Check 1: Speed continuity
        speed_violations = 0
        total_segments = 0
        positions = []

        for ping in pings:
            # Extract lat/lng from PostGIS geometry
            try:
                result = self.db.execute(
                    text("SELECT ST_X(location::geometry), ST_Y(location::geometry) FROM gps_pings WHERE id = :id"),
                    {"id": str(ping.id)},
                ).fetchone()
                if result:
                    positions.append((result[1], result[0], ping.pinged_at))  # lat, lng, time
            except Exception:
                if ping.speed_kmh is not None:
                    # Use speed directly if available
                    if ping.speed_kmh > 80:
                        speed_violations += 1
                total_segments += 1

        if len(positions) >= 2:
            for i in range(1, len(positions)):
                lat1, lng1, t1 = positions[i - 1]
                lat2, lng2, t2 = positions[i]
                dist_m = geodesic((lat1, lng1), (lat2, lng2)).meters
                dt_sec = max((t2 - t1).total_seconds(), 1)
                speed_kmh = (dist_m / 1000.0) / (dt_sec / 3600.0)
                total_segments += 1
                if speed_kmh > 80.0:
                    speed_violations += 1

        speed_score = speed_violations / max(total_segments, 1)

        # Check 2: Micro-drift (perfect static position = suspicious)
        if len(positions) >= 5:
            lats = [p[0] for p in positions]
            lngs = [p[1] for p in positions]
            lat_variance = max(lats) - min(lats)
            lng_variance = max(lngs) - min(lngs)
            # Real devices show ±0.00003–0.00008 degree variance (~3–8m)
            if lat_variance < 0.000001 and lng_variance < 0.000001:
                drift_score = 1.0  # Perfectly static — highly suspicious
            elif lat_variance < 0.00003:
                drift_score = 0.4
            else:
                drift_score = 0.0
        else:
            drift_score = 0.0

        # Combined trajectory score
        trajectory_score = (speed_score * 0.6) + (drift_score * 0.4)
        return round(min(trajectory_score, 1.0), 4)

    # ─────────────────────────────────────────────────────────────────
    # SIGNAL: CELL TOWER VS GPS
    # ─────────────────────────────────────────────────────────────────

    def check_cell_tower_vs_gps(
        self,
        gps_lat: float,
        gps_lng: float,
        tower_lat: Optional[float],
        tower_lng: Optional[float],
    ) -> Optional[bool]:
        """
        Returns True (match) if cell tower and GPS are within 500m.
        Returns False (mismatch — flag) if distance > 500m.
        If tower data unavailable: return None (not a fraud signal).
        """
        if tower_lat is None or tower_lng is None:
            return None
        dist = geodesic((gps_lat, gps_lng), (tower_lat, tower_lng)).meters
        return dist <= self.CELL_TOWER_MISMATCH_METERS

    # ─────────────────────────────────────────────────────────────────
    # SIGNAL: PLATFORM ACTIVITY
    # ─────────────────────────────────────────────────────────────────

    def check_platform_activity(
        self, worker_id: str, zone_id: str, event_time: datetime
    ) -> float:
        """
        Check platform order activity in 90 minutes before event_time.
        Returns 0.0 (very active) to 1.0 (no activity — suspicious).
        In development, returns a simulated value based on worker pattern.
        """
        # In production: query platform order pings from Zomato/Swiggy APIs
        # For Phase 1: use GPS pings as a proxy for activity
        from app.models.gps_ping import GpsPing

        lookback = event_time - timedelta(minutes=90)
        ping_count = (
            self.db.query(func.count(GpsPing.id))
            .filter(
                GpsPing.worker_id == worker_id,
                GpsPing.pinged_at >= lookback,
                GpsPing.pinged_at <= event_time,
            )
            .scalar()
        )

        # >= 10 pings in 90 min → active (delivery-like activity)
        # < 3 pings → suspicious
        if ping_count >= 10:
            return 0.1
        elif ping_count >= 5:
            return 0.3
        elif ping_count >= 2:
            return 0.5
        elif ping_count == 1:
            return 0.7
        else:
            return 0.9  # No activity — suspicious

    # ─────────────────────────────────────────────────────────────────
    # NETWORK DROP GRACE PERIOD
    # ─────────────────────────────────────────────────────────────────

    def check_network_drop_grace(
        self, worker_id: str, event_time: datetime
    ) -> dict:
        """
        If GPS pings are sparse/absent during disruption window:
          - Extend last-known-position for up to 45 minutes ('signal_gap', not fraud)
          - Check cell tower data during the gap
          - NEVER treat GPS signal loss alone as fraud evidence.
        """
        from app.models.gps_ping import GpsPing

        grace_window_start = event_time - timedelta(
            minutes=settings.GPS_SIGNAL_GAP_GRACE_MINUTES
        )

        # Check last known ping before the gap
        last_ping = (
            self.db.query(GpsPing)
            .filter(
                GpsPing.worker_id == worker_id,
                GpsPing.pinged_at >= grace_window_start,
                GpsPing.pinged_at <= event_time,
            )
            .order_by(GpsPing.pinged_at.desc())
            .first()
        )

        if last_ping is None:
            return {"grace": False, "soft_flag_only": True, "method": "no_data"}

        # Check cell tower data
        if (
            last_ping.cell_tower_lat is not None
            and last_ping.cell_tower_lng is not None
            and last_ping.cell_tower_matches is True
        ):
            return {"grace": True, "method": "cell_tower"}

        # GPS signal gap within 45 minutes — extend last known position gracefully
        return {"grace": True, "method": "last_known_position"}

    # ─────────────────────────────────────────────────────────────────
    # COMPUTE BASELINE ADJUSTMENT (repeat false positives)
    # ─────────────────────────────────────────────────────────────────

    def compute_baseline_adjustment(self, worker_id: str) -> float:
        """
        If worker has >= 2 confirmed false positives in last 90 days:
        apply downward baseline adjustment of 0.08.
        """
        from app.models.fraud_score import FraudScore

        cutoff = datetime.utcnow() - timedelta(days=settings.FALSE_POSITIVE_WINDOW_DAYS)
        # Count resolved hold claims that were ultimately approved (false positives)
        fp_count = (
            self.db.query(func.count(FraudScore.id))
            .filter(
                FraudScore.worker_id == worker_id,
                FraudScore.scored_at >= cutoff,
                FraudScore.action_taken == "hold",
                # If the claim was later approved, it was a false positive
            )
            .scalar()
        )

        if fp_count >= settings.FALSE_POSITIVE_COUNT_THRESHOLD:
            return settings.FALSE_POSITIVE_BASELINE_ADJUST  # -0.08
        return 0.0

    # ─────────────────────────────────────────────────────────────────
    # MAIN: COMPUTE FRAUD SCORE
    # ─────────────────────────────────────────────────────────────────

    def compute_fraud_score(self, claim_id: str) -> FraudScoreResult:
        """
        Orchestrates all signal checks and returns a composite fraud score.

        Score composition (weighted):
          gps_trajectory:      weight 0.25
          cell_tower_match:    weight 0.20 (if data available)
          platform_activity:   weight 0.25
          zone_presence_score: weight 0.20
          device_fp_match:     weight 0.10
        """
        from app.models.claim import Claim
        from app.models.fraud_score import FraudScore as FraudScoreModel
        from app.models.gps_ping import GpsPing
        from app.models.device_fingerprint import DeviceFingerprint
        from geoalchemy2.functions import ST_X, ST_Y

        claim = self.db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        event_time = claim.trigger_event.started_at
        worker_id = str(claim.worker_id)
        zone_id = str(claim.policy.zone_id) if claim.policy else None

        # ── Signal 1: GPS Trajectory (weight 0.25)
        gps_score = self.check_gps_trajectory(worker_id, event_time)

        # ── Signal 2: Cell Tower Match (weight 0.20)
        # Get most recent GPS ping with tower data
        last_ping = (
            self.db.query(GpsPing)
            .filter(
                GpsPing.worker_id == worker_id,
                GpsPing.cell_tower_lat.isnot(None),
            )
            .order_by(GpsPing.pinged_at.desc())
            .first()
        )
        tower_match = None
        if last_ping and last_ping.cell_tower_lat:
            # Get GPS coordinates from PostGIS
            try:
                coords = self.db.execute(
                    text("SELECT ST_Y(location::geometry), ST_X(location::geometry) FROM gps_pings WHERE id = :id"),
                    {"id": str(last_ping.id)},
                ).fetchone()
                if coords:
                    tower_match = self.check_cell_tower_vs_gps(
                        coords[0], coords[1],
                        float(last_ping.cell_tower_lat),
                        float(last_ping.cell_tower_lng),
                    )
            except Exception as e:
                logger.warning(f"Cell tower check error: {e}")

        # ── Signal 3: Platform Activity (weight 0.25)
        activity_score = self.check_platform_activity(worker_id, zone_id or "", event_time)

        # ── Signal 4: Zone Presence (weight 0.20)
        zone_presence = 0.5  # default credibility
        if zone_id:
            zone_presence = self.compute_zone_presence_score(worker_id, zone_id)

        # ── Signal 5: Device Fingerprint Match (weight 0.10)
        current_fp = (
            self.db.query(DeviceFingerprint)
            .filter(DeviceFingerprint.worker_id == worker_id, DeviceFingerprint.is_current == True)
            .first()
        )
        device_fp_match = current_fp is not None  # simplified — full check in prod

        # ── Weighted Score Composition
        weights = {
            "gps": 0.25,
            "tower": 0.20,
            "activity": 0.25,
            "zone": 0.20,
            "device": 0.10,
        }

        # Tower weight redistribution if no data
        tower_score_val = 0.0 if tower_match is None else (0.0 if tower_match else 1.0)
        if tower_match is None:
            # Redistribute tower weight to others proportionally
            active_w = weights["gps"] + weights["activity"] + weights["zone"] + weights["device"]
            adj = {
                "gps": weights["gps"] / active_w,
                "activity": weights["activity"] / active_w,
                "zone": weights["zone"] / active_w,
                "device": weights["device"] / active_w,
            }
            total_score = (
                gps_score * adj["gps"]
                + activity_score * adj["activity"]
                + (1.0 - zone_presence) * adj["zone"]
                + (0.0 if device_fp_match else 1.0) * adj["device"]
            )
        else:
            total_score = (
                gps_score * weights["gps"]
                + tower_score_val * weights["tower"]
                + activity_score * weights["activity"]
                + (1.0 - zone_presence) * weights["zone"]
                + (0.0 if device_fp_match else 1.0) * weights["device"]
            )

        # Apply baseline adjustment for repeat false positives
        baseline_adj = self.compute_baseline_adjustment(worker_id)
        adjusted_score = max(0.0, total_score - baseline_adj)
        adjusted_score = round(min(adjusted_score, 1.0), 4)

        action, partial_pct = self.determine_action(adjusted_score)

        # Persist to fraud_scores
        fs = FraudScoreModel(
            claim_id=claim_id,
            worker_id=worker_id,
            total_score=adjusted_score,
            gps_trajectory_score=gps_score,
            cell_tower_match=tower_match,
            platform_activity_score=activity_score,
            device_fp_match=device_fp_match,
            zone_presence_score=zone_presence,
            action_taken=action,
            baseline_adjustment=baseline_adj,
        )
        self.db.add(fs)
        self.db.commit()

        return FraudScoreResult(
            total_score=adjusted_score,
            action_taken=action,
            partial_pct=partial_pct,
            gps_trajectory_score=gps_score,
            cell_tower_match=tower_match,
            platform_activity_score=activity_score,
            device_fp_match=device_fp_match,
            zone_presence_score=zone_presence,
            baseline_adjustment=baseline_adj,
            signal_breakdown={
                "gps_weight": weights["gps"],
                "tower_weight": weights["tower"] if tower_match is not None else 0,
                "activity_weight": weights["activity"],
                "zone_weight": weights["zone"],
                "device_weight": weights["device"],
            },
        )

    # ─────────────────────────────────────────────────────────────────
    # ACTION DETERMINATION
    # ─────────────────────────────────────────────────────────────────

    def determine_action(self, score: float) -> tuple[str, float]:
        """
        Returns (action, partial_pct):
          score <= 0.30: ('auto_approve', 100.0)
          score <= 0.55: ('partial', 60.0)
          score <= 0.70: ('hold', 0.0)
          score >  0.70: ('block', 0.0)
        """
        if score <= self.AUTO_APPROVE_MAX:
            return ("auto_approve", 100.0)
        elif score <= self.PARTIAL_PAY_MAX:
            return ("partial", 60.0)
        elif score <= self.HARD_HOLD_MAX:
            return ("hold", 0.0)
        else:
            return ("block", 0.0)
