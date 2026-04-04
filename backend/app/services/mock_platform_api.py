"""
Mock Platform API — Simulates Zomato/Swiggy Partner API responses.
Schema-compatible with real partner APIs — swap with one config line in production.
"""
import random
from datetime import datetime, timedelta, date
from typing import List, Dict, Any


class MockPlatformAPI:
    """
    Deterministic mock of Zomato/Swiggy Partner API for demo purposes.
    All data is seeded with a fixed RNG so results are reproducible.
    """

    DEMO_WORKERS = {
        "ravi_kondapur": {
            "zomato": {"dae": 820.0, "active_days": 87, "zone": "Kondapur"},
            "swiggy": {"dae": 180.0, "active_days": 62, "zone": "Kondapur"},
        }
    }

    REST_DAYS = [15, 42, 67]  # Days off out of 90

    def __init__(self, platform: str = "zomato"):
        self.platform = platform
        self._rng = random.Random(42)

    # ─────────────────────────────────────────────────────────────────
    # SETTLEMENT DATA (90 days)
    # ─────────────────────────────────────────────────────────────────

    def get_settlements_90d(self, worker_handle: str = "ravi_kondapur") -> List[Dict]:
        """
        Returns 90 days of daily settlement records.
        Schema matches Zomato Partner API `/partner/v2/delivery-partners/{id}/settlements`
        """
        config = self.DEMO_WORKERS.get(worker_handle, {}).get(self.platform, {})
        target_dae = config.get("dae", 820.0)
        rng = random.Random(hash(worker_handle + self.platform))

        settlements = []
        today = date.today()

        for day_offset in range(90):
            settlement_date = today - timedelta(days=90 - day_offset)
            if day_offset in self.REST_DAYS:
                continue  # rest day — no settlement

            # Realistic variance: ±25% around target DAE
            variance = rng.uniform(0.75, 1.25)
            amount = round(target_dae * variance, 2)

            settlements.append({
                "date": settlement_date.isoformat(),
                "partner_id": f"demo_{self.platform}_{worker_handle}",
                "platform": self.platform,
                "gross_earnings": amount,
                "deliveries_completed": rng.randint(8, 22),
                "active_hours": round(rng.uniform(5.0, 9.5), 1),
                "zone": config.get("zone", "Kondapur"),
                "settlement_status": "completed",
                # Real API fields for future compatibility
                "tip_amount": round(rng.uniform(0, 50), 2),
                "surge_bonus": round(rng.uniform(0, 80), 2),
                "tax_deducted": round(amount * 0.02, 2),
                "net_settlement": round(amount * 0.98, 2),
            })

        return settlements

    def get_dae(self, worker_handle: str = "ravi_kondapur") -> Dict[str, Any]:
        """
        Compute DAE from settlement data.
        Returns schema compatible with EarningsEngine.
        """
        settlements = self.get_settlements_90d(worker_handle)
        total = sum(s["gross_earnings"] for s in settlements)
        active_days = len(settlements)

        dae_raw = total / active_days if active_days > 0 else 0.0
        # Cold-start discount
        if active_days < 30:
            import math
            dae_adj = dae_raw * math.sqrt(active_days / 30.0)
        else:
            dae_adj = min(dae_raw, 2000.0)  # Hard cap

        return {
            "platform": self.platform,
            "worker_handle": worker_handle,
            "dae_raw": round(dae_raw, 2),
            "dae_adjusted": round(dae_adj, 2),
            "active_days_90d": active_days,
            "total_settlements_90d": round(total, 2),
            "cold_start_applied": active_days < 30,
            "hard_cap_applied": dae_raw > 2000.0,
        }

    # ─────────────────────────────────────────────────────────────────
    # GPS ACTIVITY HISTORY
    # ─────────────────────────────────────────────────────────────────

    def get_gps_history(self, worker_handle: str = "ravi_kondapur", days: int = 1) -> List[Dict]:
        """
        Returns GPS activity history for fraud gate cross-validation.
        Pings are road-following with natural ±5m drift.
        Schema compatible with Zomato Partner Location Feed API.
        """
        config = self.DEMO_WORKERS.get(worker_handle, {}).get("zomato", {})
        zone = config.get("zone", "Kondapur")

        # Kondapur centroid
        ZONE_CENTERS = {
            "Kondapur": (17.4600, 78.3650),
        }
        base_lat, base_lng = ZONE_CENTERS.get(zone, (17.4600, 78.3650))

        rng = random.Random(hash(worker_handle + "gps"))
        pings = []
        now = datetime.utcnow()

        for day_offset in range(days):
            base_time = now - timedelta(days=day_offset, hours=4)
            # 12 pings over an 8-hour shift
            for i in range(12):
                t = base_time + timedelta(minutes=i * 40 + rng.randint(-5, 5))
                lat = base_lat + rng.uniform(-0.006, 0.006) + rng.gauss(0, 0.00004)
                lng = base_lng + rng.uniform(-0.006, 0.006) + rng.gauss(0, 0.00004)
                pings.append({
                    "timestamp": t.isoformat() + "Z",
                    "latitude": round(lat, 7),
                    "longitude": round(lng, 7),
                    "accuracy_m": round(rng.uniform(3.5, 12.0), 1),
                    "speed_kmh": round(rng.uniform(8.0, 28.0), 1),
                    "altitude_m": round(rng.uniform(530, 555), 1),  # Hyderabad elevation
                    "zone": zone,
                    "on_delivery": rng.random() > 0.3,
                    "network_type": rng.choice(["4G", "4G", "4G", "3G"]),
                    "cell_tower_id": f"AIRTEL-HYD-{rng.randint(100, 999)}",
                })

        return pings

    # ─────────────────────────────────────────────────────────────────
    # ORDER VOLUME (for trigger cross-validation)
    # ─────────────────────────────────────────────────────────────────

    def get_zone_order_volume(self, zone: str, hours_back: int = 1) -> Dict:
        """
        Returns simulated order volume data for a zone.
        Used by trigger monitor to compute order drop %.
        """
        rng = random.Random(hash(zone + str(datetime.utcnow().hour)))
        baseline = rng.randint(120, 200)
        # During demo: 35% drop (simulating rainfall disruption)
        current = int(baseline * 0.65)
        return {
            "zone": zone,
            "baseline_orders_per_hour": baseline,
            "current_orders": current,
            "drop_pct": round((1 - current / baseline) * 100, 1),
            "window_hours": hours_back,
            "timestamp": datetime.utcnow().isoformat(),
        }

    # ─────────────────────────────────────────────────────────────────
    # WORKER STATUS (for platform activity check in fraud gate)
    # ─────────────────────────────────────────────────────────────────

    def get_worker_status(self, worker_handle: str = "ravi_kondapur") -> Dict:
        """Active session check — used by fraud gate platform_activity signal."""
        return {
            "partner_id": f"demo_zomato_{worker_handle}",
            "status": "active",
            "last_ping_minutes_ago": 12,
            "current_zone": "Kondapur",
            "active_order_id": "ORD-2026-DEMO-001",
            "session_since": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
        }
