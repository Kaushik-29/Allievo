"""
Dynamic Premium Engine
======================
Implements Section 2 of the plan spec exactly.

Sunday at 23:00 IST — computes the next week's premium for all
workers on the 'dynamic' plan using a 7-day OpenWeatherMap forecast.

Standalone class — can be called from:
  - Celery Beat task (production)
  - Admin endpoint (demo/manual trigger)
  - Direct import (tests)
"""
import logging
import httpx
from datetime import date, datetime, timedelta
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Worker baseline (overridden per-worker in production via profile)
HOURLY_RATE = 80.0     # ₹ per hour

# Plan definitions (kept in sync with plans table seed)
PLAN_DEFS = {
    "basic": {
        "days_per_week": 2, "hours_per_day": 2, "covered_hours": 4,
        "premium_rate": 0.15, "plan_value": HOURLY_RATE * 4,  # ₹320
        "max_payout": HOURLY_RATE * 4,
    },
    "dynamic": {
        "days_per_week": 3, "hours_per_day": 4, "covered_hours": 12,
        "premium_rate": None,  # computed dynamically
        "plan_value": HOURLY_RATE * 12,  # ₹960
        "max_payout": HOURLY_RATE * 12,
    },
    "premium": {
        "days_per_week": 4, "hours_per_day": 6, "covered_hours": 24,
        "premium_rate": 0.30, "plan_value": HOURLY_RATE * 24,  # ₹1,920
        "max_payout": HOURLY_RATE * 24,
    },
}

BASIC_PLAN_VALUE = PLAN_DEFS["basic"]["plan_value"]       # ₹320
BASIC_WEEKLY_PREMIUM = BASIC_PLAN_VALUE * 0.15            # ₹48
DYNAMIC_PLAN_VALUE = PLAN_DEFS["dynamic"]["plan_value"]   # ₹960
DYNAMIC_PREMIUM_CAP = DYNAMIC_PLAN_VALUE * 0.25           # ₹240 = 25% of plan value


class DynamicPremiumEngine:
    """
    Computes the dynamic weekly premium via OpenWeatherMap forecasts.
    Falls back gracefully if API key is 'mock' or request fails.
    """

    OWM_BASE = "https://api.openweathermap.org/data/2.5"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENWEATHERMAP_API_KEY
        self.mock_mode = (self.api_key == "mock" or not self.api_key)

    # ─────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────

    def compute_dynamic_premium(
        self,
        lat: float = 17.4647,
        lon: float = 78.3513,
        last_week_multiplier: float = 1.0,
        hourly_rate: float = HOURLY_RATE,
    ) -> dict:
        """
        Main entry point — returns the full premium computation result.

        Returns:
          {
            premium_amount: float,
            week_risk_score: float,
            peak_rain_mm: float,
            peak_temp_c: float,
            peak_aqi: float,
            multiplier_applied: float,
            plain_reason: str,
            forecast_breakdown: { rain_score, temp_score, aqi_score }
          }
        """
        basic_premium = BASIC_PLAN_VALUE * 0.15  # ₹48 (fixed regardless of hourly_rate for now)

        if self.mock_mode:
            return self._mock_result(basic_premium)

        # 1. Fetch weather forecast
        forecast_slots = self._fetch_5day_forecast(lat, lon)
        # 2. Fetch AQI forecast
        aqi_slots = self._fetch_aqi_forecast(lat, lon)

        if not forecast_slots:
            logger.warning("No forecast data, using mock fallback")
            return self._mock_result(basic_premium)

        # 3. Compute risk per slot
        slot_risks = []
        peak_rain = 0.0
        peak_temp = -999.0
        peak_aqi_val = 0.0

        for i, slot in enumerate(forecast_slots):
            rain_mm_hr = slot.get("rain_mm_hr", 0.0)
            temp_c = slot.get("temp_c", 25.0)
            # Try to match AQI slot by index
            aqi_val = aqi_slots[i]["aqi"] if i < len(aqi_slots) else 85.0

            r_score = self._rain_score(rain_mm_hr)
            t_score = self._temp_score(temp_c)
            a_score = self._aqi_score(aqi_val)

            slot_risk = 0.50 * r_score + 0.30 * t_score + 0.20 * a_score
            slot_risks.append(slot_risk)

            if rain_mm_hr > peak_rain:
                peak_rain = rain_mm_hr
            if temp_c > peak_temp:
                peak_temp = temp_c
            if aqi_val > peak_aqi_val:
                peak_aqi_val = aqi_val

        # 4. Aggregate
        peak_risk = max(slot_risks)
        avg_risk = sum(slot_risks) / len(slot_risks)
        week_risk = 0.60 * peak_risk + 0.40 * avg_risk
        week_risk = max(0.05, min(0.95, week_risk))

        # 5. Multiplier
        base_mult = 1.05 + (week_risk * 0.95)  # range 1.05–2.00
        if last_week_multiplier > 1.50:
            base_mult = max(1.30, base_mult)

        dynamic_premium = basic_premium * base_mult
        dynamic_premium = max(basic_premium * 1.05, dynamic_premium)
        dynamic_premium = min(DYNAMIC_PREMIUM_CAP, dynamic_premium)

        # 6. Plain reason
        plain_reason = self._plain_reason(peak_rain, peak_temp, peak_aqi_val)

        return {
            "premium_amount":   round(dynamic_premium, 2),
            "week_risk_score":  round(week_risk, 4),
            "peak_rain_mm":     round(peak_rain, 2),
            "peak_temp_c":      round(peak_temp, 1),
            "peak_aqi":         round(peak_aqi_val, 1),
            "multiplier_applied": round(base_mult, 4),
            "plain_reason":     plain_reason,
            "forecast_breakdown": {
                "rain_score": round(self._rain_score(peak_rain), 3),
                "temp_score": round(self._temp_score(peak_temp), 3),
                "aqi_score":  round(self._aqi_score(peak_aqi_val), 3),
            },
        }

    def get_static_premium(self, plan_name: str, hourly_rate: float = HOURLY_RATE) -> float:
        """Return the fixed weekly premium for basic/premium plans."""
        p = PLAN_DEFS.get(plan_name)
        if not p or p["premium_rate"] is None:
            raise ValueError(f"Use compute_dynamic_premium() for plan '{plan_name}'")
        return round(p["plan_value"] * p["premium_rate"], 2)

    def get_forecast_risk_bars(self, lat: float = 17.4647, lon: float = 78.3513) -> dict:
        """
        Lightweight call for the frontend plan card — returns the three risk bars
        and the current multiplier WITHOUT writing to DB.
        """
        if self.mock_mode:
            return self._mock_risk_bars()

        try:
            result = self.compute_dynamic_premium(lat, lon)
            return {
                "rain_bar":   result["forecast_breakdown"]["rain_score"],
                "temp_bar":   result["forecast_breakdown"]["temp_score"],
                "aqi_bar":    result["forecast_breakdown"]["aqi_score"],
                "multiplier": result["multiplier_applied"],
                "plain_reason": result["plain_reason"],
                "current_premium": result["premium_amount"],
            }
        except Exception as e:
            logger.error(f"forecast_risk_bars failed: {e}")
            return self._mock_risk_bars()

    # ─────────────────────────────────────────────────────────────
    # INTERNAL FETCH METHODS
    # ─────────────────────────────────────────────────────────────

    def _fetch_5day_forecast(self, lat: float, lon: float) -> list[dict]:
        """Fetch OWM 5-day/3-hr forecast, return list of {rain_mm_hr, temp_c}."""
        url = f"{self.OWM_BASE}/forecast"
        params = {"lat": lat, "lon": lon, "appid": self.api_key, "units": "metric"}
        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.get(url, params=params)
                r.raise_for_status()
                data = r.json()
        except Exception as e:
            logger.warning(f"OWM forecast fetch failed: {e}")
            return []

        slots = []
        cutoff = datetime.utcnow() + timedelta(days=7)
        for item in data.get("list", []):
            dt = datetime.utcfromtimestamp(item["dt"])
            if dt > cutoff:
                break
            rain_3h = item.get("rain", {}).get("3h", 0.0)
            slots.append({
                "dt":         dt,
                "rain_mm_hr": rain_3h / 3.0,       # Convert 3hr total to per-hour
                "temp_c":     item["main"]["temp"],
            })
        return slots

    def _fetch_aqi_forecast(self, lat: float, lon: float) -> list[dict]:
        """Fetch OWM Air Pollution forecast, return list of {aqi}."""
        url = "http://api.openweathermap.org/data/2.5/air_pollution/forecast"
        params = {"lat": lat, "lon": lon, "appid": self.api_key}
        try:
            with httpx.Client(timeout=10.0) as client:
                r = client.get(url, params=params)
                r.raise_for_status()
                data = r.json()
        except Exception as e:
            logger.warning(f"OWM AQI forecast fetch failed: {e}")
            return []

        slots = []
        for item in data.get("list", []):
            pm25 = item.get("components", {}).get("pm2_5", 10.0)
            slots.append({"aqi": self._pm25_to_aqi(pm25)})
        return slots

    # ─────────────────────────────────────────────────────────────
    # RISK SCORING HELPERS
    # ─────────────────────────────────────────────────────────────

    @staticmethod
    def _pm25_to_aqi(pm25: float) -> float:
        """Convert PM2.5 μg/m³ to AQI scale (0–500)."""
        if pm25 <= 12:     return pm25 / 12 * 50
        if pm25 <= 35.4:   return 50 + (pm25 - 12) / 23.4 * 50
        if pm25 <= 55.4:   return 100 + (pm25 - 35.4) / 20 * 50
        if pm25 <= 150:    return 150 + (pm25 - 55.4) / 94.6 * 100
        if pm25 <= 250:    return 250 + (pm25 - 150) / 100 * 100
        return min(500, 350 + (pm25 - 250) / 150 * 150)

    @staticmethod
    def _rain_score(mm_hr: float) -> float:
        if mm_hr < 40:  return mm_hr / 120
        if mm_hr < 65:  return 0.33 + (mm_hr - 40) / 75 * 0.34
        return min(1.0, 0.67 + (mm_hr - 65) / 55 * 0.33)

    @staticmethod
    def _temp_score(c: float) -> float:
        if c < 40: return 0.0
        return min(1.0, (c - 40) / 10)

    @staticmethod
    def _aqi_score(aqi: float) -> float:
        return min(1.0, aqi / 500)

    @staticmethod
    def _plain_reason(peak_rain: float, peak_temp: float, peak_aqi: float) -> str:
        if peak_rain > 65:
            return f"Heavy rain forecast ({peak_rain:.0f}mm/hr) in your zone."
        if peak_temp >= 44:
            return f"Heat advisory forecast ({peak_temp:.0f}°C) this week."
        if peak_aqi >= 400:
            return f"Severe AQI forecast ({peak_aqi:.0f}) expected this week."
        return "Normal week — standard rate applied."

    # ─────────────────────────────────────────────────────────────
    # MOCK FALLBACKS
    # ─────────────────────────────────────────────────────────────

    def _mock_result(self, basic_premium: float) -> dict:
        """Simulates a moderate-risk week (multiplier ~1.35)."""
        multiplier = 1.35
        premium = round(min(basic_premium * multiplier, DYNAMIC_PREMIUM_CAP), 2)
        return {
            "premium_amount":    premium,
            "week_risk_score":   0.32,
            "peak_rain_mm":      28.0,
            "peak_temp_c":       36.0,
            "peak_aqi":          142.0,
            "multiplier_applied": multiplier,
            "plain_reason":      "Normal week — standard rate applied. (mock mode)",
            "forecast_breakdown": {"rain_score": 0.23, "temp_score": 0.0, "aqi_score": 0.28},
        }

    def _mock_risk_bars(self) -> dict:
        return {
            "rain_bar":       0.23,
            "temp_bar":       0.0,
            "aqi_bar":        0.28,
            "multiplier":     1.35,
            "plain_reason":   "Normal week — standard rate applied. (mock mode)",
            "current_premium": round(BASIC_WEEKLY_PREMIUM * 1.35, 2),
        }


# ─────────────────────────────────────────────────────────────────
# PLAN CATALOGUE HELPERS (used by the /plans API)
# ─────────────────────────────────────────────────────────────────

def get_all_plans_with_premiums(
    lat: float = 17.4647,
    lon: float = 78.3513,
) -> list[dict]:
    """
    Returns the full plan list with dynamic premium computed live.
    Used by GET /api/v1/plans.
    """
    engine = DynamicPremiumEngine()

    plans = []

    # Basic
    plans.append({
        "name":          "basic",
        "label":         "Basic",
        "badge_color":   "blue",
        "days_per_week": 2,
        "hours_per_day": 2,
        "covered_hours": 4,
        "plan_value":    320.0,
        "max_payout":    320.0,
        "weekly_premium": 48.0,    # fixed: ₹320 × 15%
        "premium_rate":  0.15,
        "claim_mode":    "manual_or_auto",
        "claim_label":   "You choose",
        "description":   "2 days × 2 hrs covered. Manually select your claim window after disruption.",
        "forecast_bars": None,
    })

    # Dynamic
    forecast_bars = engine.get_forecast_risk_bars(lat, lon)
    plans.append({
        "name":          "dynamic",
        "label":         "Dynamic",
        "badge_color":   "green",
        "days_per_week": 3,
        "hours_per_day": 4,
        "covered_hours": 12,
        "plan_value":    960.0,
        "max_payout":    960.0,
        "weekly_premium": forecast_bars["current_premium"],
        "premium_rate":  None,
        "claim_mode":    "auto_only",
        "claim_label":   "Automatic",
        "description":   "3 days × 4 hrs covered. Premium adjusts each week based on 7-day weather forecast.",
        "forecast_bars": forecast_bars,
        "popular":       True,
    })

    # Premium
    plans.append({
        "name":          "premium",
        "label":         "Premium",
        "badge_color":   "amber",
        "days_per_week": 4,
        "hours_per_day": 6,
        "covered_hours": 24,
        "plan_value":    1920.0,
        "max_payout":    1920.0,
        "weekly_premium": 576.0,   # fixed: ₹1,920 × 30%
        "premium_rate":  0.30,
        "claim_mode":    "auto_only",
        "claim_label":   "Automatic",
        "description":   "4 days × 6 hrs covered. Maximum protection with priority fraud review.",
        "forecast_bars": None,
    })

    return plans
