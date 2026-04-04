"""
Payout Pipeline — Section 4.6
Orchestrates claim creation, fraud gate, and UPI transfers.
"""
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import httpx
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.services.earnings_engine import EarningsEngine
from app.services.fraud_gate import FraudGate
from app.services.ring_detector import RingDetector
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class PayoutPipeline:

    MANDATORY_GATE_SECONDS = settings.MANDATORY_GATE_SECONDS  # 300 seconds (5 min)

    def __init__(self, db: Session):
        self.db = db
        self.earnings_engine = EarningsEngine()
        self.notification_service = NotificationService()

    # ─────────────────────────────────────────────────────────────────
    # MAIN ORCHESTRATION
    # ─────────────────────────────────────────────────────────────────

    def process_trigger_event(self, trigger_event_id: str):
        """
        Main orchestration. Called by Celery task when trigger is detected.
        Steps 1–8 as defined in Section 4.6.
        """
        from app.models.trigger_event import TriggerEvent
        from app.models.policy import Policy
        from app.models.claim import Claim
        from app.models.earnings_snapshot import EarningsSnapshot
        from app.models.worker import Worker

        trigger = self.db.query(TriggerEvent).filter(TriggerEvent.id == trigger_event_id).first()
        if not trigger:
            logger.error(f"Trigger event {trigger_event_id} not found")
            return

        # ── Step 1: Find all eligible workers in zone with active policies
        eligible_policies = (
            self.db.query(Policy)
            .filter(
                Policy.zone_id == trigger.zone_id,
                Policy.status == "active",
                Policy.eligible_for_payout == True,
                Policy.week_start <= trigger.started_at.date(),
                Policy.week_end >= trigger.started_at.date(),
            )
            .all()
        )

        if not eligible_policies:
            logger.info(f"No eligible workers for trigger {trigger_event_id}")
            return

        logger.info(f"Processing {len(eligible_policies)} eligible workers for trigger {trigger_event_id}")

        # ── Step 2–3: For each worker, compute payout and create claim
        claims_created = []
        for policy in eligible_policies:
            worker = self.db.query(Worker).filter(Worker.id == policy.worker_id).first()
            if not worker:
                continue

            # Get combined DAE for worker
            dae = self._get_worker_dae(str(policy.worker_id))
            if dae == 0:
                logger.warning(f"Worker {policy.worker_id} has zero DAE — skipping")
                continue

            # Compute disruption hours
            disruption_hours = float(trigger.duration_hours or 4.0)
            working_hours = float(policy.coverage_hours_day)

            # Get weekly paid so far
            weekly_paid = self.earnings_engine.compute_weekly_paid_so_far(
                str(policy.worker_id), str(policy.id), self.db
            )

            # Trailing 12-week premiums for aggregate cap
            trailing_premiums = self._compute_trailing_premiums(str(policy.worker_id))
            per_event_cap = self.earnings_engine.compute_per_event_aggregate_cap(trailing_premiums)

            payout_calc = self.earnings_engine.compute_payout(
                dae=dae,
                disruption_hours=disruption_hours,
                working_hours=working_hours,
                coverage_factor=float(policy.coverage_factor),
                severity_multiplier=float(trigger.severity_multiplier),
                weekly_cap=float(policy.max_weekly_payout),
                weekly_paid_so_far=weekly_paid,
                per_event_aggregate_cap=per_event_cap,
            )

            claim = Claim(
                worker_id=policy.worker_id,
                policy_id=policy.id,
                trigger_event_id=trigger_event_id,
                dae_used=dae,
                disruption_hours=disruption_hours,
                working_hours=working_hours,
                coverage_factor=float(policy.coverage_factor),
                severity_multiplier=float(trigger.severity_multiplier),
                gross_payout=payout_calc["gross_payout"],
                capped_payout=payout_calc["capped_payout"],
                status="pending",
                platform_scope="all",
                calculation_log=payout_calc["calculation_log"],
            )
            self.db.add(claim)
            claims_created.append((claim, worker, policy))

        self.db.commit()

        # ── Step 4: Wait mandatory 5-minute fraud gate
        logger.info(f"Fraud gate waiting {self.MANDATORY_GATE_SECONDS}s for trigger {trigger_event_id}")
        time.sleep(self.MANDATORY_GATE_SECONDS)

        # Refresh claims from DB (status may have changed)
        self.db.expire_all()

        # ── Step 5: Run ring detection across all claimants
        claimant_worker_ids = [str(c.worker_id) for c, _, _ in claims_created]
        ring_detector = RingDetector(self.db)
        ring_result = ring_detector.run_ring_detection(trigger_event_id, claimant_worker_ids)

        ring_blocked_workers = set(ring_result.affected_workers) if ring_result.alert_created else set()

        # ── Steps 6–7: Score each claim and initiate payouts
        for claim, worker, policy in claims_created:
            # Refresh claim
            self.db.refresh(claim)

            if claim.status == "blocked":
                logger.info(f"Claim {claim.id} blocked by ring detection — skipping")
                continue

            if str(claim.worker_id) in ring_blocked_workers:
                continue

            # Run fraud gate
            try:
                fraud_result = FraudGate(self.db).compute_fraud_score(str(claim.id))
            except Exception as e:
                logger.error(f"Fraud gate error for claim {claim.id}: {e}")
                continue

            # Update claim status
            if fraud_result.action_taken == "auto_approve":
                claim.status = "approved"
                self.db.commit()
                self._initiate_full_payout(claim, worker)

            elif fraud_result.action_taken == "partial":
                claim.status = "partial"
                self.db.commit()
                self._initiate_partial_payout(claim, worker)

            elif fraud_result.action_taken == "hold":
                claim.status = "held"
                self.db.commit()
                self.notification_service.send_hard_hold_notification(
                    worker, claim, trigger
                )

            else:  # block
                claim.status = "blocked"
                self.db.commit()
                logger.warning(f"Claim {claim.id} blocked — high fraud score {fraud_result.total_score}")

            # ── Step 8: Send worker notification
            self.notification_service.send_claim_notification(
                worker=worker,
                claim=claim,
                action=fraud_result.action_taken,
                trigger=trigger,
            )

    # ─────────────────────────────────────────────────────────────────
    # UPI TRANSFER
    # ─────────────────────────────────────────────────────────────────

    def initiate_upi_transfer(
        self, payout_id: str, amount: float, upi_vpa: str
    ):
        """
        Calls Razorpay Transfer API. Updates payout status accordingly.
        Retries up to 3 times with exponential backoff on failure.
        """
        from app.models.payout import Payout

        payout = self.db.query(Payout).filter(Payout.id == payout_id).first()
        if not payout:
            return

        payout.initiated_at = datetime.utcnow()
        payout.status = "initiated"
        self.db.commit()

        max_retries = 3
        for attempt in range(max_retries):
            try:
                transfer_id, success = self._call_razorpay(amount, upi_vpa)
                if success:
                    payout.razorpay_transfer_id = transfer_id
                    payout.status = "success"
                    payout.completed_at = datetime.utcnow()
                    self.db.commit()
                    logger.info(f"UPI transfer success: {transfer_id} ₹{amount} → {upi_vpa}")
                    return
                else:
                    raise Exception("Razorpay returned failure")
            except Exception as e:
                logger.error(f"UPI transfer attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # exponential backoff: 1s, 2s, 4s

        payout.status = "failed"
        payout.failure_reason = "All 3 retry attempts exhausted"
        self.db.commit()

    def _call_razorpay(self, amount: float, upi_vpa: str) -> tuple[str, bool]:
        """
        Call Razorpay Payout API.
        In development mode, simulates success.
        """
        if settings.ENVIRONMENT == "development":
            # Simulate Razorpay sandbox
            import uuid
            transfer_id = f"rzp_payout_{uuid.uuid4().hex[:16]}"
            logger.info(f"[MOCK] Razorpay transfer: {transfer_id} ₹{amount} → {upi_vpa}")
            return transfer_id, True

        try:
            resp = httpx.post(
                "https://api.razorpay.com/v1/payouts",
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
                json={
                    "account_number": "2323230072190834",  # your Razorpay X account
                    "fund_account": {
                        "account_type": "vpa",
                        "vpa": {"address": upi_vpa},
                        "contact": {"name": "Allievo Payout"},
                    },
                    "amount": int(amount * 100),  # paise
                    "currency": "INR",
                    "mode": "UPI",
                    "purpose": "payout",
                    "queue_if_low_balance": True,
                    "narration": "Allievo Insurance Payout",
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("id", ""), data.get("status") == "processed"
        except Exception as e:
            logger.error(f"Razorpay API error: {e}")
            raise

    # ─────────────────────────────────────────────────────────────────
    # PARTIAL PAYOUT
    # ─────────────────────────────────────────────────────────────────

    def _initiate_full_payout(self, claim, worker):
        """Initiate 100% UPI transfer for auto-approved claims."""
        from app.models.payout import Payout
        from app.models.upi_graph import UpiGraph

        upi = (
            self.db.query(UpiGraph)
            .filter(UpiGraph.worker_id == worker.id, UpiGraph.is_primary == True)
            .first()
        )
        if not upi:
            logger.error(f"No UPI for worker {worker.id}")
            return

        payout = Payout(
            claim_id=claim.id,
            worker_id=worker.id,
            upi_vpa=upi.upi_vpa,
            amount=claim.capped_payout,
            payout_type="full",
        )
        self.db.add(payout)
        self.db.commit()
        self.initiate_upi_transfer(str(payout.id), float(claim.capped_payout), upi.upi_vpa)

    def _initiate_partial_payout(self, claim, worker):
        """Initiate 60% now, schedule 40% for 24hr later."""
        from app.models.payout import Payout
        from app.models.upi_graph import UpiGraph

        upi = (
            self.db.query(UpiGraph)
            .filter(UpiGraph.worker_id == worker.id, UpiGraph.is_primary == True)
            .first()
        )
        if not upi:
            return

        first_amount = round(float(claim.capped_payout) * (settings.PARTIAL_PAY_FIRST_PCT / 100), 2)
        held_amount = round(float(claim.capped_payout) - first_amount, 2)

        # First payment (60%)
        payout_first = Payout(
            claim_id=claim.id,
            worker_id=worker.id,
            upi_vpa=upi.upi_vpa,
            amount=first_amount,
            payout_type="partial_first",
        )
        self.db.add(payout_first)

        # Held payment (40%) — scheduled for 24hr later
        release_at = datetime.utcnow() + timedelta(hours=settings.PARTIAL_RELEASE_HOURS)
        payout_second = Payout(
            claim_id=claim.id,
            worker_id=worker.id,
            upi_vpa=upi.upi_vpa,
            amount=held_amount,
            payout_type="partial_second",
            release_scheduled_at=release_at,
            release_status="pending",
        )
        self.db.add(payout_second)
        self.db.commit()

        self.initiate_upi_transfer(str(payout_first.id), first_amount, upi.upi_vpa)
        self.schedule_partial_release(str(payout_second.id), held_amount, release_at)

    def schedule_partial_release(
        self, payout_id: str, held_amount: float, release_at: datetime
    ):
        """Schedule the Celery task for partial payout release at 24hr."""
        from app.workers.reconciliation import release_held_payout
        release_held_payout.apply_async(
            args=[payout_id],
            eta=release_at,
        )

    # ─────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────

    def _get_worker_dae(self, worker_id: str) -> float:
        """Get combined DAE across all platforms for a worker."""
        from app.models.earnings_snapshot import EarningsSnapshot

        snapshots = (
            self.db.query(EarningsSnapshot)
            .filter(EarningsSnapshot.worker_id == worker_id)
            .all()
        )

        if not snapshots:
            return 0.0

        platform_daes = {s.platform: float(s.dae_confidence_adj) for s in snapshots}
        return self.earnings_engine.compute_combined_dae(platform_daes)

    def _compute_trailing_premiums(self, worker_id: str) -> float:
        """Sum of premiums paid in last 12 weeks."""
        from app.models.policy import Policy

        cutoff = datetime.utcnow() - timedelta(weeks=12)
        total = (
            self.db.query(func.sum(Policy.premium_paid))
            .filter(
                Policy.worker_id == worker_id,
                Policy.week_start >= cutoff.date(),
                Policy.status.in_(["active", "expired"]),
            )
            .scalar()
        )
        return float(total or 0.0)
