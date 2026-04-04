"""
Razorpay Client — Sandbox/Mock UPI Payout Integration.
In demo mode (RAZORPAY_KEY_ID starts with 'rzp_test_mock'): returns realistic mock responses.
In production: uses live Razorpay Payout API.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

RAZORPAY_BASE = "https://api.razorpay.com/v1"


class RazorpayClient:

    def __init__(self):
        self.key_id = settings.RAZORPAY_KEY_ID
        self.key_secret = settings.RAZORPAY_KEY_SECRET
        self._mock_mode = self.key_id.startswith("rzp_test_mock")
        self._auth = (self.key_id, self.key_secret)

    # ─────────────────────────────────────────────────────────────────
    # FUND ACCOUNT (required before payout)
    # ─────────────────────────────────────────────────────────────────

    def create_fund_account(self, worker_id: str, upi_vpa: str, name: str) -> Dict[str, Any]:
        """
        Creates a Razorpay Fund Account for the worker's UPI VPA.
        Returns fund_account_id for use in payouts.
        """
        if self._mock_mode:
            fa_id = f"fa_demo_{worker_id[:8]}"
            logger.info(f"[MOCK] Fund account created: {fa_id} for UPI {upi_vpa}")
            return {
                "id": fa_id,
                "entity": "fund_account",
                "contact_id": f"cont_demo_{worker_id[:8]}",
                "account_type": "vpa",
                "vpa": {"address": upi_vpa},
                "active": True,
                "mock": True,
            }

        try:
            # Step 1: Create contact
            contact_resp = httpx.post(
                f"{RAZORPAY_BASE}/contacts",
                json={"name": name, "type": "vendor", "reference_id": worker_id},
                auth=self._auth,
                timeout=15,
            )
            contact_id = contact_resp.json()["id"]

            # Step 2: Create fund account
            fa_resp = httpx.post(
                f"{RAZORPAY_BASE}/fund_accounts",
                json={
                    "contact_id": contact_id,
                    "account_type": "vpa",
                    "vpa": {"address": upi_vpa},
                },
                auth=self._auth,
                timeout=15,
            )
            return fa_resp.json()
        except Exception as e:
            logger.error(f"Razorpay fund account error: {e}")
            raise

    # ─────────────────────────────────────────────────────────────────
    # PAYOUT
    # ─────────────────────────────────────────────────────────────────

    def initiate_payout(
        self,
        fund_account_id: str,
        amount_inr: float,
        purpose: str = "payout",
        narration: str = "Allievo Insurance Payout",
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Initiates a UPI payout via Razorpay.
        amount_inr: Amount in INR (will be converted to paise).
        Returns Razorpay payout object with transfer_id.
        """
        amount_paise = int(amount_inr * 100)
        idem_key = idempotency_key or str(uuid.uuid4())

        if self._mock_mode:
            transfer_id = f"pout_demo_{uuid.uuid4().hex[:16]}"
            logger.info(
                f"[MOCK] Razorpay payout: ₹{amount_inr} → {fund_account_id} "
                f"| ref={transfer_id}"
            )
            return {
                "id": transfer_id,
                "entity": "payout",
                "fund_account_id": fund_account_id,
                "amount": amount_paise,
                "currency": "INR",
                "status": "processed",
                "mode": "UPI",
                "purpose": purpose,
                "narration": narration,
                "utr": f"UTR{uuid.uuid4().hex[:18].upper()}",
                "created_at": int(datetime.utcnow().timestamp()),
                "processed_at": int(datetime.utcnow().timestamp()),
                "mock": True,
            }

        try:
            resp = httpx.post(
                f"{RAZORPAY_BASE}/payouts",
                json={
                    "account_number": "2323230093590124",  # From Razorpay X account
                    "fund_account_id": fund_account_id,
                    "amount": amount_paise,
                    "currency": "INR",
                    "mode": "UPI",
                    "purpose": purpose,
                    "narration": narration,
                    "queue_if_low_balance": True,
                },
                headers={"X-Payout-Idempotency": idem_key},
                auth=self._auth,
                timeout=20,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Razorpay payout error: {e}")
            raise

    # ─────────────────────────────────────────────────────────────────
    # STATUS CHECK
    # ─────────────────────────────────────────────────────────────────

    def get_payout_status(self, payout_id: str) -> str:
        """Returns 'processed'|'failed'|'pending'|'queued'."""
        if self._mock_mode:
            return "processed"
        try:
            resp = httpx.get(f"{RAZORPAY_BASE}/payouts/{payout_id}", auth=self._auth, timeout=10)
            return resp.json().get("status", "unknown")
        except Exception as e:
            logger.error(f"Razorpay status check error: {e}")
            return "unknown"
