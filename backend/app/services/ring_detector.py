"""
Ring Detector — Section 4.5
Detects organized fraud rings via 5 independent signals.
"""
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RingDetectionResult:
    trigger_event_id: str
    signal_count: int
    signals_fired: list[str]
    affected_workers: list[str]
    alert_created: bool
    device_clusters: list = field(default_factory=list)
    upi_clusters: list = field(default_factory=list)


class RingDetector:

    RING_ALERT_THRESHOLD = settings.RING_ALERT_MIN_SIGNALS          # 3
    TEMPORAL_BURST_WINDOW_MIN = settings.RING_TEMPORAL_BURST_WINDOW_MINUTES  # 3
    TEMPORAL_BURST_MIN_CLAIMS = settings.RING_TEMPORAL_BURST_MIN_CLAIMS      # 5
    DEVICE_SHARE_LOOKBACK_DAYS = settings.DEVICE_SHARE_LOOKBACK_DAYS         # 30
    REFERRAL_RING_THRESHOLD = settings.RING_REFERRAL_CHAIN_THRESHOLD         # 8

    def __init__(self, db: Session):
        self.db = db

    # ─────────────────────────────────────────────────────────────────
    # SIGNAL 1: DEVICE SHARING
    # ─────────────────────────────────────────────────────────────────

    def check_device_sharing(self, worker_ids: list[str]) -> list[tuple]:
        """
        Query device_fingerprints for all workers in a disruption event.
        If any 3+ accounts share a hardware ID in last 30 days → ring signal.
        Returns list of (hardware_id_hash, [worker_ids]) tuples.
        """
        from app.models.device_fingerprint import DeviceFingerprint

        cutoff = datetime.utcnow() - timedelta(days=self.DEVICE_SHARE_LOOKBACK_DAYS)

        fps = (
            self.db.query(
                DeviceFingerprint.hardware_id_hash,
                DeviceFingerprint.worker_id,
            )
            .filter(
                DeviceFingerprint.worker_id.in_(worker_ids),
                DeviceFingerprint.captured_at >= cutoff,
            )
            .all()
        )

        # Group by hardware_id_hash
        hash_to_workers = defaultdict(list)
        for hw_hash, worker_id in fps:
            hash_to_workers[hw_hash].append(str(worker_id))

        clusters = [
            (hw_hash, list(set(workers)))
            for hw_hash, workers in hash_to_workers.items()
            if len(set(workers)) >= 3
        ]
        return clusters

    # ─────────────────────────────────────────────────────────────────
    # SIGNAL 2: UPI CLUSTERING
    # ─────────────────────────────────────────────────────────────────

    def check_upi_clustering(
        self, worker_ids: list[str], trigger_event_id: str
    ) -> list[tuple]:
        """
        Detect:
          1. Multiple workers mapping to same UPI VPA
          2. UPI accounts registered within 48 hours of this trigger event
        """
        from app.models.upi_graph import UpiGraph
        from app.models.trigger_event import TriggerEvent

        trigger = (
            self.db.query(TriggerEvent)
            .filter(TriggerEvent.id == trigger_event_id)
            .first()
        )
        if not trigger:
            return []

        suspect_window_start = trigger.created_at - timedelta(
            hours=settings.UPI_NEW_REGISTRATION_HOURS
        )

        vpas = (
            self.db.query(UpiGraph.upi_vpa, UpiGraph.worker_id, UpiGraph.registered_at)
            .filter(UpiGraph.worker_id.in_(worker_ids))
            .all()
        )

        vpa_to_workers = defaultdict(list)
        for vpa, worker_id, registered_at in vpas:
            is_new = registered_at >= suspect_window_start if registered_at else False
            vpa_to_workers[vpa].append({"worker_id": str(worker_id), "new_registration": is_new})

        clusters = [
            (vpa, workers)
            for vpa, workers in vpa_to_workers.items()
            if len(workers) > 1 or any(w["new_registration"] for w in workers)
        ]
        return clusters

    # ─────────────────────────────────────────────────────────────────
    # SIGNAL 3: TEMPORAL BURST
    # ─────────────────────────────────────────────────────────────────

    def check_temporal_burst(self, trigger_event_id: str) -> bool:
        """
        Query claims created for this trigger_event_id.
        If >= 5 claims created within any 3-minute window AND
        all have GPS pings in zone within last 15 minutes → burst signal.
        """
        from app.models.claim import Claim

        claims = (
            self.db.query(Claim)
            .filter(Claim.trigger_event_id == trigger_event_id)
            .order_by(Claim.auto_generated_at.asc())
            .all()
        )

        if len(claims) < self.TEMPORAL_BURST_MIN_CLAIMS:
            return False

        times = [c.auto_generated_at for c in claims]
        window_secs = self.TEMPORAL_BURST_WINDOW_MIN * 60

        # Sliding window: check if >= 5 claims fall within any 3-min window
        for i in range(len(times)):
            window_end = times[i] + timedelta(seconds=window_secs)
            count_in_window = sum(1 for t in times if times[i] <= t <= window_end)
            if count_in_window >= self.TEMPORAL_BURST_MIN_CLAIMS:
                return True

        return False

    # ─────────────────────────────────────────────────────────────────
    # SIGNAL 4: REFERRAL CHAIN
    # ─────────────────────────────────────────────────────────────────

    def check_referral_chain(
        self, worker_ids: list[str], trigger_event_id: str
    ) -> bool:
        """
        Walk referral_graph. Check if >= 8 workers in this event's
        claimants belong to the same referral subtree (BFS from each root).
        """
        from app.models.referral_graph import ReferralGraph

        all_ref_edges = self.db.query(ReferralGraph).all()

        # Build adjacency list (referrer → [referred])
        adj: dict[str, list[str]] = defaultdict(list)
        all_nodes = set()
        for edge in all_ref_edges:
            referrer = str(edge.referrer_worker_id) if edge.referrer_worker_id else None
            referred = str(edge.referred_worker_id)
            all_nodes.add(referred)
            if referrer:
                adj[referrer].append(referred)
                all_nodes.add(referrer)

        # Find root nodes (workers who were not referred by anyone)
        referred_set = {str(e.referred_worker_id) for e in all_ref_edges}
        roots = [n for n in all_nodes if n not in referred_set]

        worker_set = set(worker_ids)

        for root in roots:
            # BFS from this root
            subtree = set()
            queue = deque([root])
            while queue:
                node = queue.popleft()
                if node in subtree:
                    continue
                subtree.add(node)
                for child in adj.get(node, []):
                    queue.append(child)

            # Count how many claimants are in this subtree
            overlap = subtree & worker_set
            if len(overlap) >= self.REFERRAL_RING_THRESHOLD:
                return True

        return False

    # ─────────────────────────────────────────────────────────────────
    # SIGNAL 5: GPS PROXIMITY CLUSTERING
    # ─────────────────────────────────────────────────────────────────

    def check_gps_proximity_clustering(
        self, worker_ids: list[str], event_time: datetime
    ) -> bool:
        """
        Query gps_pings for all workers in the 15 min before event_time.
        If >= 10 accounts report identical coordinates (within 10m of each other)
        → proximity clustering ring signal.
        """
        lookback = event_time - timedelta(minutes=15)

        try:
            result = self.db.execute(
                text("""
                    WITH recent_pings AS (
                        SELECT worker_id, location
                        FROM gps_pings
                        WHERE worker_id = ANY(:worker_ids)
                          AND pinged_at BETWEEN :lookback AND :event_time
                    )
                    SELECT COUNT(DISTINCT rp1.worker_id) as cluster_count
                    FROM recent_pings rp1, recent_pings rp2
                    WHERE rp1.worker_id != rp2.worker_id
                      AND ST_DWithin(
                            rp1.location::geography,
                            rp2.location::geography,
                            :threshold_meters
                          )
                """),
                {
                    "worker_ids": [str(w) for w in worker_ids],
                    "lookback": lookback,
                    "event_time": event_time,
                    "threshold_meters": settings.RING_GPS_PROXIMITY_THRESHOLD_METERS,
                },
            )
            cluster_count = result.scalar() or 0
            return cluster_count >= settings.RING_GPS_PROXIMITY_MIN_ACCOUNTS
        except Exception as e:
            logger.warning(f"GPS proximity check error: {e}")
            return False

    # ─────────────────────────────────────────────────────────────────
    # ORCHESTRATION
    # ─────────────────────────────────────────────────────────────────

    def run_ring_detection(
        self, trigger_event_id: str, worker_ids: list[str]
    ) -> RingDetectionResult:
        """
        Runs all 5 checks. If signal_count >= threshold:
          → Create ring_alert record
          → Set all affected claim statuses to 'blocked'
          → Notify human review queue
        """
        from app.models.ring_alert import RingAlert
        from app.models.claim import Claim
        from app.models.trigger_event import TriggerEvent

        signals_fired = []
        device_clusters = []
        upi_clusters = []
        all_affected = set()

        trigger = (
            self.db.query(TriggerEvent)
            .filter(TriggerEvent.id == trigger_event_id)
            .first()
        )
        event_time = trigger.started_at if trigger else datetime.utcnow()

        # ── Check 1: Device sharing
        dc = self.check_device_sharing(worker_ids)
        if dc:
            signals_fired.append("device_sharing")
            device_clusters = dc
            for _, workers in dc:
                all_affected.update(workers)

        # ── Check 2: UPI clustering
        uc = self.check_upi_clustering(worker_ids, trigger_event_id)
        if uc:
            signals_fired.append("upi_clustering")
            upi_clusters = uc
            for _, workers in uc:
                for w in workers:
                    all_affected.add(w["worker_id"])

        # ── Check 3: Temporal burst
        if self.check_temporal_burst(trigger_event_id):
            signals_fired.append("temporal_burst")
            all_affected.update(worker_ids)

        # ── Check 4: Referral chain
        if self.check_referral_chain(worker_ids, trigger_event_id):
            signals_fired.append("referral_chain")
            all_affected.update(worker_ids)

        # ── Check 5: GPS proximity
        if self.check_gps_proximity_clustering(worker_ids, event_time):
            signals_fired.append("gps_proximity_clustering")
            all_affected.update(worker_ids)

        signal_count = len(signals_fired)
        alert_created = False

        if signal_count >= self.RING_ALERT_THRESHOLD:
            # Create ring_alert
            ring_alert = RingAlert(
                trigger_event_id=trigger_event_id,
                worker_ids=list(all_affected),
                device_ids=[dc[0] for dc, _ in device_clusters] if device_clusters else [],
                upi_vpas=[vpa for vpa, _ in upi_clusters] if upi_clusters else [],
                signals_fired=signals_fired,
                signal_count=signal_count,
                status="open",
            )
            self.db.add(ring_alert)

            # Block all affected claims
            self.db.query(Claim).filter(
                Claim.trigger_event_id == trigger_event_id,
                Claim.worker_id.in_(list(all_affected)),
            ).update({"status": "blocked"}, synchronize_session=False)

            self.db.commit()
            alert_created = True
            logger.warning(
                f"RING ALERT created for trigger {trigger_event_id}: "
                f"{signal_count} signals, {len(all_affected)} affected workers"
            )

            # Notify review queue
            self._notify_review_queue(trigger_event_id, list(all_affected), signals_fired)

        return RingDetectionResult(
            trigger_event_id=trigger_event_id,
            signal_count=signal_count,
            signals_fired=signals_fired,
            affected_workers=list(all_affected),
            alert_created=alert_created,
            device_clusters=device_clusters,
            upi_clusters=upi_clusters,
        )

    def _notify_review_queue(
        self,
        trigger_event_id: str,
        affected_workers: list[str],
        signals: list[str],
    ):
        """Notify human review queue via webhook."""
        import httpx
        try:
            httpx.post(
                settings.ADMIN_WEBHOOK_URL,
                json={
                    "event": "ring_alert",
                    "trigger_event_id": trigger_event_id,
                    "affected_workers": len(affected_workers),
                    "signals": signals,
                    "priority": "high",
                },
                timeout=5,
            )
        except Exception as e:
            logger.error(f"Review queue notification failed: {e}")
