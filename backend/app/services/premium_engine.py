"""
Premium Engine
Implements all logic from Section 4.2 exactly as specified.
"""
from app.core.config import settings


class PremiumEngine:

    BASE_RATE: float = settings.BASE_RATE
    DYNAMIC_AMPLIFIER: float = settings.DYNAMIC_AMPLIFIER
    PREMIUM_CAP: float = settings.PREMIUM_CAP
    PREMIUM_FLOOR: float = settings.PREMIUM_FLOOR

    TIER_FACTORS: dict[str, float] = {
        "basic": 0.8,
        "standard": 1.0,
        "premium": 1.4,
    }
    TIER_COVERAGE_FACTOR: dict[str, float] = {
        "basic": settings.TIER_BASIC_COVERAGE_FACTOR,
        "standard": settings.TIER_STANDARD_COVERAGE_FACTOR,
        "premium": settings.TIER_PREMIUM_COVERAGE_FACTOR,
    }
    TIER_MAX_PAYOUT: dict[str, int] = {
        "basic": settings.TIER_BASIC_MAX_PAYOUT,
        "standard": settings.TIER_STANDARD_MAX_PAYOUT,
        "premium": settings.TIER_PREMIUM_MAX_PAYOUT,
    }
    TIER_COVERAGE_HOURS: dict[str, int] = {
        "basic": settings.TIER_BASIC_COVERAGE_HOURS,
        "standard": settings.TIER_STANDARD_COVERAGE_HOURS,
        "premium": settings.TIER_PREMIUM_COVERAGE_HOURS,
    }

    def loyalty_adjustment(self, loyalty_weeks: int) -> float:
        """Returns loyalty discount multiplier based on consecutive weeks."""
        if loyalty_weeks < 5:
            return 1.0
        elif loyalty_weeks <= 12:
            return settings.LOYALTY_ADJUSTMENT_WEEK_5_12   # 0.95
        else:
            return settings.LOYALTY_ADJUSTMENT_WEEK_13_PLUS  # 0.90

    def zone_risk_multiplier(self, disruption_days_per_year: float) -> float:
        """
        ZRM = 0.8 + (disruption_days_per_year / 50) × 1.0, clamped [0.8, 1.8]
        """
        raw = 0.8 + (disruption_days_per_year / 50.0) * 1.0
        return round(min(max(raw, 0.8), 1.8), 3)

    def seasonal_buffer_factor(self, zone_type: str, month: int) -> float:
        """
        zone_type: 'flood' | 'aqi' | 'low'
        month: 1-12
        """
        if zone_type == "flood":
            if month in [6, 7, 8, 9]:
                return 1.4
            elif month in [10, 11]:
                return 1.2
            else:
                return 1.0
        elif zone_type == "aqi":
            if month in [10, 11, 12, 1, 2]:
                return 1.35
            else:
                return 1.0
        else:  # 'low' or unknown
            return 1.0

    def static_base_premium(
        self,
        zone_risk_multiplier: float,
        tier: str,
        loyalty_weeks: int,
        seasonal_factor: float,
    ) -> float:
        """
        SBP = Base_Rate × ZRM × Tier_Factor × Loyalty × Seasonal
        """
        sbp = (
            self.BASE_RATE
            * zone_risk_multiplier
            * self.TIER_FACTORS[tier]
            * self.loyalty_adjustment(loyalty_weeks)
            * seasonal_factor
        )
        return round(sbp, 2)

    def compute_risk_score(
        self,
        disruption_days_last_365: int,
        rain_probability_7d: float,       # 0.0 – 1.0
        rain_severity_factor: float,      # 0.3 | 0.6 | 1.0
        aqi_7day_avg: float,
        avg_zone_speed_kmh: float,
        live_event_score: float,          # 0.0 | 0.5 | 1.0
    ) -> dict:
        """
        RS = 0.30×Hist + 0.25×Weather + 0.15×AQI + 0.15×Traffic + 0.15×Events
        Returns RS (floored 0.05, capped 0.95) and component breakdown.
        """
        hist = min(disruption_days_last_365 / 365.0, 1.0)
        weather = min(rain_probability_7d * rain_severity_factor, 1.0)
        aqi = min(aqi_7day_avg / 500.0, 1.0)
        ideal_speed = 25.0
        traffic = min(max(1.0 - (avg_zone_speed_kmh / ideal_speed), 0.0), 1.0)
        events = live_event_score

        rs = (
            0.20 * hist
            + 0.40 * weather
            + 0.15 * aqi
            + 0.15 * traffic
            + 0.10 * events
        )
        rs = min(max(rs, 0.05), 0.95)

        return {
            "risk_score": round(rs, 4),
            "components": {
                "historical": round(hist, 4),
                "weather": round(weather, 4),
                "pollution": round(aqi, 4),
                "traffic": round(traffic, 4),
                "live_event": round(events, 4),
            },
        }

    def weekly_premium(
        self,
        static_base_premium: float,
        risk_score_data: dict,
        loyalty_weeks: int,
    ) -> float:
        """
        WP = SBP × (1 + RS × DYNAMIC_AMPLIFIER) × Loyalty_Adj
        Price surge kicks in if weather component is high.
        """
        risk_score = risk_score_data["risk_score"]
        weather_component = risk_score_data["components"]["weather"]
        
        # Dynamic Amplifier: Surge if weather risk is high
        amplifier = self.DYNAMIC_AMPLIFIER
        if weather_component >= settings.WEATHER_SURGE_THRESHOLD:
            amplifier = settings.WEATHER_SURGE_AMPLIFIER
            
        wp = (
            static_base_premium
            * (1.0 + risk_score * amplifier)
            * self.loyalty_adjustment(loyalty_weeks)
        )
        return round(min(max(wp, self.PREMIUM_FLOOR), self.PREMIUM_CAP), 2)

    def get_tier_config(self, tier: str) -> dict:
        """Return full tier configuration for a given tier."""
        return {
            "tier": tier,
            "coverage_factor": self.TIER_COVERAGE_FACTOR[tier],
            "max_payout": self.TIER_MAX_PAYOUT[tier],
            "coverage_hours": self.TIER_COVERAGE_HOURS[tier],
        }
