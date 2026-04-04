"""
Trigger Monitor — Section 4.3
Polls all 5 trigger types: rainfall, heat, AQI, curfew, platform outage.
In development mode, uses mock API responses.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import httpx
from sqlalchemy.orm import Session
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TriggerResult:
    trigger_type: str
    zone_id: str
    severity_level: str
    severity_multiplier: float
    raw_value: float
    source_api: str
    secondary_confirmed: bool
    order_drop_pct: float
    duration_hours: Optional[float] = None


class TriggerMonitor:

    def __init__(self, db: Session):
        self.db = db
        self._mock_mode = settings.ENVIRONMENT == "development"

    # ─────────────────────────────────────────────────────────────────
    # TRIGGER 1: RAINFALL
    # ─────────────────────────────────────────────────────────────────

    def check_rainfall(self, zone) -> Optional[TriggerResult]:
        """
        Source 1: IMD Open API
        Source 2: OpenWeatherMap (cross-validation)
        Condition: rainfall >= 65 mm/hr OR active IMD red alert for zone
        Validation: zone order volume drops > 30% within 60 min
        Severity multiplier:
          65–80 mm/hr  → 0.8 (Moderate)
          > 80 mm/hr   → 1.0 (Heavy)
          Active flood alert → 1.0 (Heavy) regardless of mm/hr
        """
        if self._mock_mode:
            rainfall_mm = self._mock_imd_rainfall(zone)
            red_alert = self._mock_imd_red_alert(zone)
        else:
            rainfall_mm = self._fetch_imd_rainfall(zone)
            red_alert = self._fetch_imd_red_alert(zone)

        # Check trigger condition
        if rainfall_mm < settings.RAINFALL_TRIGGER_MM_PER_HOUR and not red_alert:
            return None

        # Cross-validate with OpenWeatherMap
        if settings.OPENWEATHERMAP_API_KEY == "mock":
            owm_rain = self._mock_owm_rainfall(zone)
        else:
            owm_rain = self._fetch_owm_rainfall(zone)

        # Validate order drop
        order_drop = self.compute_order_drop_pct(
            str(zone.id), settings.ORDER_DROP_WINDOW_MINUTES
        )
        if order_drop < settings.RAINFALL_ORDER_DROP_PCT and not red_alert:
            return None

        # Determine severity
        if red_alert or rainfall_mm > settings.RAINFALL_MODERATE_MAX:
            severity_level = "high"
            severity_multiplier = 1.0
        else:
            severity_level = "moderate"
            severity_multiplier = 0.8

        return TriggerResult(
            trigger_type="rainfall",
            zone_id=str(zone.id),
            severity_level=severity_level,
            severity_multiplier=severity_multiplier,
            raw_value=rainfall_mm,
            source_api="imd",
            secondary_confirmed=owm_rain >= settings.RAINFALL_TRIGGER_MM_PER_HOUR,
            order_drop_pct=order_drop,
        )

    # ─────────────────────────────────────────────────────────────────
    # TRIGGER 2: EXTREME HEAT
    # ─────────────────────────────────────────────────────────────────

    def check_heat(self, zone) -> Optional[TriggerResult]:
        """
        Condition: temp >= 44°C AND active IMD heat advisory
        Validation: platform heat suspension notice OR order drop > 40%
        Payout duration: per 2-hour block
        Severity multiplier: 0.85
        """
        if settings.OPENWEATHERMAP_API_KEY == "mock":
            temp_celsius = self._mock_temperature(zone)
        else:
            temp_celsius = self._fetch_temperature(zone)
            
        if self._mock_mode:
            heat_advisory = self._mock_heat_advisory(zone)
        else:
            heat_advisory = self._fetch_heat_advisory(zone)

        if temp_celsius < settings.HEAT_TRIGGER_CELSIUS or not heat_advisory:
            return None

        order_drop = self.compute_order_drop_pct(
            str(zone.id), settings.ORDER_DROP_WINDOW_MINUTES
        )
        platform_suspension = self._check_platform_heat_suspension(zone)

        if order_drop < 40.0 and not platform_suspension:
            return None

        return TriggerResult(
            trigger_type="heat",
            zone_id=str(zone.id),
            severity_level="moderate",
            severity_multiplier=0.85,
            raw_value=temp_celsius,
            source_api="imd",
            secondary_confirmed=platform_suspension,
            order_drop_pct=order_drop,
        )

    # ─────────────────────────────────────────────────────────────────
    # TRIGGER 3: AQI
    # ─────────────────────────────────────────────────────────────────

    def check_aqi(self, zone) -> Optional[TriggerResult]:
        """
        Source: CPCB API (primary), AQI.in (secondary)
        Condition: AQI > 400 sustained >= 4 hours
        Validation: GRAP restriction level from govt notification API
        Severity multiplier:
          401–450 → 0.85
          451+    → 1.0
        Payout: full day payout per qualifying day
        """
        if self._mock_mode:
            aqi_value = self._mock_cpcb_aqi(zone)
            sustained_hours = self._mock_aqi_sustained_hours(zone)
            grap_confirmed = self._mock_grap_restriction(zone)
        else:
            aqi_value = self._fetch_cpcb_aqi(zone)
            sustained_hours = self._fetch_aqi_sustained_hours(zone)
            grap_confirmed = self._fetch_grap_restriction(zone)

        if aqi_value <= settings.AQI_TRIGGER_THRESHOLD:
            return None
        if sustained_hours < settings.AQI_SUSTAINED_HOURS:
            return None

        # Determine severity
        if aqi_value <= settings.AQI_MODERATE_MAX:
            severity_level = "moderate"
            severity_multiplier = 0.85
        else:
            severity_level = "high"
            severity_multiplier = 1.0

        order_drop = self.compute_order_drop_pct(str(zone.id), 240)  # 4-hour window

        return TriggerResult(
            trigger_type="aqi",
            zone_id=str(zone.id),
            severity_level=severity_level,
            severity_multiplier=severity_multiplier,
            raw_value=aqi_value,
            source_api="cpcb",
            secondary_confirmed=grap_confirmed,
            order_drop_pct=order_drop,
            duration_hours=24.0,  # full day payout
        )

    # ─────────────────────────────────────────────────────────────────
    # TRIGGER 4: CURFEW / BANDH
    # ─────────────────────────────────────────────────────────────────

    def check_curfew(self, zone) -> Optional[TriggerResult]:
        """
        Source: Government notification feed (NDMA API) + verified news API
        Condition: Section 144 / state bandh confirmed in worker zone
        Validation: order volume drops > 80% within 1 hour of event
        Severity multiplier: 1.0
        Payout: full official restriction duration
        """
        if self._mock_mode:
            curfew_active, duration_hours = self._mock_govt_curfew(zone)
        else:
            curfew_active, duration_hours = self._fetch_govt_curfew(zone)

        if not curfew_active:
            return None

        order_drop = self.compute_order_drop_pct(str(zone.id), 60)
        if order_drop < settings.CURFEW_ORDER_DROP_PCT:
            return None

        return TriggerResult(
            trigger_type="curfew",
            zone_id=str(zone.id),
            severity_level="high",
            severity_multiplier=1.0,
            raw_value=1.0,
            source_api="govt",
            secondary_confirmed=True,
            order_drop_pct=order_drop,
            duration_hours=duration_hours,
        )

    # ─────────────────────────────────────────────────────────────────
    # TRIGGER 5: PLATFORM OUTAGE (NO DOWNDETECTOR)
    # ─────────────────────────────────────────────────────────────────

    def check_platform_outage(self, platform: str, zone) -> Optional[TriggerResult]:
        """
        Source 1: Official Zomato/Swiggy status page API (PRIMARY)
        Source 2: Pingdom/third-party infra monitor (SECONDARY)
        *** Downdetector is NOT used. Ignored entirely. ***

        Condition:
          - Official outage >= 45 min during peak hours (12–2pm OR 7–10pm IST)
          - Zone order volume drops > 30% vs 7-day same-hour average
          - >= 2 independent monitoring sources confirm outage

        Severity multiplier:
          45–90 min → 0.7
          > 90 min  → 0.9
        Payout: per hour of confirmed outage during peak windows only
        """
        # Check if current time is in peak hours (IST)
        now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
        hour_ist = now_ist.hour
        is_peak = (12 <= hour_ist < 14) or (19 <= hour_ist < 22)

        if not is_peak:
            return None

        if self._mock_mode:
            official_outage_mins = self._mock_platform_status(platform)
            pingdom_confirmed = self._mock_pingdom_status(platform)
        else:
            official_outage_mins = self._fetch_platform_status(platform)
            pingdom_confirmed = self._fetch_pingdom_status(platform)

        # Must have >= 2 independent sources confirm outage (no Downdetector)
        sources_confirmed = int(official_outage_mins >= settings.OUTAGE_MIN_MINUTES) + int(pingdom_confirmed)
        if sources_confirmed < settings.OUTAGE_MIN_SOURCES:
            return None

        if official_outage_mins < settings.OUTAGE_MIN_MINUTES:
            return None

        order_drop = self.compute_order_drop_pct(str(zone.id), settings.ORDER_DROP_WINDOW_MINUTES)
        if order_drop < settings.OUTAGE_ORDER_DROP_PCT:
            return None

        # Determine severity multiplier
        if official_outage_mins <= settings.OUTAGE_MODERATE_MAX:
            severity_level = "low"
            severity_multiplier = 0.7
        else:
            severity_level = "moderate"
            severity_multiplier = 0.9

        duration_hours = official_outage_mins / 60.0

        return TriggerResult(
            trigger_type="outage",
            zone_id=str(zone.id),
            severity_level=severity_level,
            severity_multiplier=severity_multiplier,
            raw_value=float(official_outage_mins),
            source_api=f"{platform}_status",
            secondary_confirmed=pingdom_confirmed,
            order_drop_pct=order_drop,
            duration_hours=duration_hours,
        )

    # ─────────────────────────────────────────────────────────────────
    # ORDER DROP COMPUTATION (shared across triggers)
    # ─────────────────────────────────────────────────────────────────

    def compute_order_drop_pct(self, zone_id: str, threshold_minutes: int) -> float:
        """
        Compare current order volume in zone vs 7-day rolling average
        for the same time-of-day window (±30 min).
        Returns drop as percentage (0–100).
        In mock mode, returns a simulated value.
        """
        if self._mock_mode:
            # Mock: return 35% drop to simulate an active disruption
            return 35.0

        # Real implementation: query platform order data
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=threshold_minutes)

        # This would query platform order feeds — stubbed for real integration
        current_volume = self._fetch_current_order_volume(zone_id, window_start, now)
        baseline_volume = self._fetch_baseline_order_volume(zone_id, now)

        if baseline_volume == 0:
            return 0.0

        drop_pct = max(0.0, (1.0 - current_volume / baseline_volume) * 100.0)
        return round(drop_pct, 2)

    # ─────────────────────────────────────────────────────────────────
    # POLL ALL ZONES (called by Celery Beat every 15 minutes)
    # ─────────────────────────────────────────────────────────────────

    def poll_all_zones(self) -> list[TriggerResult]:
        """Poll all active zones for any trigger conditions."""
        from app.models.zone_score import ZoneScore

        zones = self.db.query(ZoneScore).all()
        results = []

        for zone in zones:
            for check_fn in [
                self.check_rainfall,
                self.check_heat,
                self.check_aqi,
                self.check_curfew,
            ]:
                result = check_fn(zone)
                if result:
                    results.append(result)
                    logger.info(f"Trigger detected: {result.trigger_type} in zone {zone.zone_name}")

            for platform in ["zomato", "swiggy"]:
                result = self.check_platform_outage(platform, zone)
                if result:
                    results.append(result)

        return results

    # ─────────────────────────────────────────────────────────────────
    # MOCK API RESPONSES (development mode)
    # ─────────────────────────────────────────────────────────────────

    def _mock_imd_rainfall(self, zone) -> float:
        """Mock: Kondapur zone gets a heavy rainfall event."""
        if hasattr(zone, "zone_name") and "Kondapur" in zone.zone_name:
            return 72.0  # mm/hr — above threshold
        return 10.0

    def _mock_imd_red_alert(self, zone) -> bool:
        return False

    def _mock_owm_rainfall(self, zone) -> float:
        if hasattr(zone, "zone_name") and "Kondapur" in zone.zone_name:
            return 68.0
        return 8.0

    def _mock_temperature(self, zone) -> float:
        return 38.0  # Below threshold

    def _mock_heat_advisory(self, zone) -> bool:
        return False

    def _mock_cpcb_aqi(self, zone) -> float:
        if hasattr(zone, "zone_name") and "Lajpat" in zone.zone_name:
            return 420.0  # Delhi AQI trigger
        return 150.0

    def _mock_aqi_sustained_hours(self, zone) -> int:
        if hasattr(zone, "zone_name") and "Lajpat" in zone.zone_name:
            return 5
        return 0

    def _mock_grap_restriction(self, zone) -> bool:
        return True

    def _mock_govt_curfew(self, zone) -> tuple[bool, float]:
        return False, 0.0

    def _mock_platform_status(self, platform: str) -> int:
        """ Simulate a 60-min Zomato outage for demo. """
        if platform == "zomato":
            return 60  # minutes
        return 0

    def _mock_pingdom_status(self, platform: str) -> bool:
        return platform == "zomato"

    def _check_platform_heat_suspension(self, zone) -> bool:
        return False

    # ─────────────────────────────────────────────────────────────────
    # REAL API FETCH STUBS (production mode — implement with real keys)
    # ─────────────────────────────────────────────────────────────────

    def _fetch_imd_rainfall(self, zone) -> float:
        # IMD Open Data API: requires IMD_API_KEY
        try:
            resp = httpx.get(
                f"https://api.imd.gov.in/v1/rainfall",
                params={"zone": zone.zone_name, "city": zone.city},
                headers={"Authorization": f"Bearer {settings.IMD_API_KEY}"},
                timeout=10,
            )
            return float(resp.json().get("rainfall_mm_per_hour", 0))
        except Exception as e:
            logger.error(f"IMD API error: {e}")
            return 0.0

    def _fetch_imd_red_alert(self, zone) -> bool:
        return False  # Implement with real IMD alert API

    def _get_zone_centroid(self, zone) -> tuple[float, float]:
        """
        Extract lat/lon centroid from PostGIS zone_boundary.
        If boundary is missing, fall back to city center (approx).
        """
        if not zone.zone_boundary:
            # Fallback coordinates for demo cities (example: Bengaluru)
            fallbacks = {"Bengaluru": (12.9716, 77.5946), "Delhi": (28.6139, 77.2090)}
            return fallbacks.get(zone.city, (12.9716, 77.5946))

        # In production, this would use ST_X(ST_Centroid(zone_boundary)) in SQL
        # For this logic, we assume the zone object has these extracted or we mock a centroid
        return (12.97, 77.59) # Mock centroid for now

    def _fetch_owm_rainfall(self, zone) -> float:
        """Fetch 1-hour precipitation from OpenWeatherMap."""
        lat, lon = self._get_zone_centroid(zone)
        try:
            resp = httpx.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": settings.OPENWEATHERMAP_API_KEY,
                    "units": "metric"
                },
                timeout=10,
            )
            data = resp.json()
            # Precipitation in mm for the last hour
            rain = data.get("rain", {}).get("1h", 0.0)
            return float(rain)
        except Exception as e:
            logger.error(f"OpenWeatherMap Rainfall API error: {e}")
            return 0.0

    def _fetch_temperature(self, zone) -> float:
        """Fetch current temperature from OpenWeatherMap."""
        lat, lon = self._get_zone_centroid(zone)
        try:
            resp = httpx.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": settings.OPENWEATHERMAP_API_KEY,
                    "units": "metric"
                },
                timeout=10,
            )
            data = resp.json()
            temp = data.get("main", {}).get("temp", 25.0)
            return float(temp)
        except Exception as e:
            logger.error(f"OpenWeatherMap Temp API error: {e}")
            return 30.0

    def _fetch_heat_advisory(self, zone) -> bool:
        return False

    def _fetch_cpcb_aqi(self, zone) -> float:
        return 100.0  # Implement with CPCB API

    def _fetch_aqi_sustained_hours(self, zone) -> int:
        return 0

    def _fetch_grap_restriction(self, zone) -> bool:
        return False

    def _fetch_govt_curfew(self, zone) -> tuple[bool, float]:
        return False, 0.0

    def _fetch_platform_status(self, platform: str) -> int:
        return 0  # Implement with official status page API

    def _fetch_pingdom_status(self, platform: str) -> bool:
        return False

    def _fetch_current_order_volume(self, zone_id: str, start, end) -> float:
        return 100.0

    def _fetch_baseline_order_volume(self, zone_id: str, now) -> float:
        return 100.0
