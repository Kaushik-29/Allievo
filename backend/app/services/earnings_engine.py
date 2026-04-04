"""
Earnings Verification Engine
Implements all logic from Section 4.1 exactly as specified.
"""
from typing import Optional
from app.core.config import settings


class EarningsEngine:

    DAE_CAP: float = settings.DAE_HARD_CAP  # ₹2,000/day maximum

    def compute_dae(self, settlements: list[float], active_days: int) -> dict:
        """
        settlements: list of net daily settlement amounts over last 90 days
        active_days: number of days with >= 1 completed delivery

        Returns:
          dae_raw: raw average (settlements_sum / active_days)
          dae_adjusted: cold-start discounted if active_days < 30
          confidence: active_days / 90 (data completeness)
        """
        if active_days == 0:
            return {"dae_raw": 0.0, "dae_adjusted": 0.0, "confidence": 0.0}

        dae_raw = sum(settlements) / active_days
        dae_raw = min(dae_raw, self.DAE_CAP)

        # Cold-start discount: active_days < 30
        if active_days < settings.COLD_START_THRESHOLD_DAYS:
            discount_factor = (active_days / 30.0) ** 0.5
            dae_adjusted = dae_raw * discount_factor
        else:
            dae_adjusted = dae_raw

        confidence = min(active_days / 90.0, 1.0)

        return {
            "dae_raw": round(dae_raw, 2),
            "dae_adjusted": round(dae_adjusted, 2),
            "confidence": round(confidence, 3),
        }

    def compute_combined_dae(self, platform_daes: dict[str, float]) -> float:
        """
        platform_daes: {"zomato": 520.0, "swiggy": 300.0}
        Returns combined DAE (sum, capped at DAE_CAP).
        Days are NOT double-counted — each platform's DAE is independent.
        """
        total = sum(platform_daes.values())
        return round(min(total, self.DAE_CAP), 2)

    def compute_payout(
        self,
        dae: float,
        disruption_hours: float,
        working_hours: float,
        coverage_factor: float,
        severity_multiplier: float,
        weekly_cap: float,
        weekly_paid_so_far: float,
        per_event_aggregate_cap: float,
    ) -> dict:
        """
        Returns:
          gross_payout: raw calculation result
          capped_payout: after applying weekly cap and aggregate cap
          cap_applied: which cap was applied ('none'|'weekly'|'aggregate')
          calculation_log: full audit trail dict
        """
        # Core formula: DAE × (disruption_hours / working_hours) × coverage_factor × severity_multiplier
        gross = dae * (disruption_hours / working_hours) * coverage_factor * severity_multiplier
        gross = round(gross, 2)

        # Apply weekly cap (remaining capacity)
        weekly_remaining = max(0.0, weekly_cap - weekly_paid_so_far)
        after_weekly = min(gross, weekly_remaining)

        # Apply per-event aggregate cap
        capped = min(after_weekly, per_event_aggregate_cap)

        cap_applied = "none"
        if capped < gross:
            cap_applied = "weekly" if after_weekly < gross else "aggregate"

        return {
            "gross_payout": gross,
            "capped_payout": round(capped, 2),
            "cap_applied": cap_applied,
            "calculation_log": {
                "dae": dae,
                "disruption_hours": disruption_hours,
                "working_hours": working_hours,
                "coverage_factor": coverage_factor,
                "severity_multiplier": severity_multiplier,
                "weekly_cap": weekly_cap,
                "weekly_paid_so_far": weekly_paid_so_far,
                "weekly_remaining": weekly_remaining,
                "per_event_aggregate_cap": per_event_aggregate_cap,
            },
        }

    def compute_weekly_paid_so_far(
        self, worker_id: str, policy_id: str, db
    ) -> float:
        """
        Query payouts table for the current policy week to get total already paid.
        Used to enforce weekly cap for subsequent events in the same week.
        """
        from app.models.payout import Payout
        from app.models.claim import Claim
        from sqlalchemy import func

        total = (
            db.query(func.sum(Payout.amount))
            .join(Claim, Payout.claim_id == Claim.id)
            .filter(
                Claim.policy_id == policy_id,
                Payout.status.in_(["success", "initiated"]),
            )
            .scalar()
        )
        return float(total or 0.0)

    def compute_per_event_aggregate_cap(
        self, trailing_12_week_premiums: float
    ) -> float:
        """
        Per-event aggregate cap = 150% of trailing 12-week premium total.
        """
        return round(
            trailing_12_week_premiums * settings.PER_EVENT_AGGREGATE_CAP_MULTIPLIER, 2
        )
