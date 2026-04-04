"""
Severity Scorer — Section 9.3
Phase 1: Rule-based tier lookup.
Phase 2: XGBoost regressor.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class SeverityResult:
    severity: str
    multiplier: float
    trigger_type: str
    raw_value: float


class SeverityScorer:
    """
    Phase 1 (current): Rule-based tier lookup from Section 9.3.
    Returns (severity_label, multiplier) for each trigger type.
    """

    def score(self, trigger_type: str, raw_value: float, extra: dict = None) -> SeverityResult:
        """
        trigger_type: 'rainfall' | 'heat' | 'aqi' | 'curfew' | 'outage'
        raw_value: mm/hr, AQI, °C, minutes
        extra: additional context (e.g. {'flood_alert': True})
        """
        extra = extra or {}

        if trigger_type == "rainfall":
            return self._score_rainfall(raw_value, extra)
        elif trigger_type == "heat":
            return self._score_heat(raw_value)
        elif trigger_type == "aqi":
            return self._score_aqi(raw_value)
        elif trigger_type == "curfew":
            return SeverityResult("high", 1.0, "curfew", raw_value)
        elif trigger_type == "outage":
            return self._score_outage(raw_value)
        else:
            return SeverityResult("low", 0.5, trigger_type, raw_value)

    def _score_rainfall(self, mm_per_hour: float, extra: dict) -> SeverityResult:
        if extra.get("flood_alert"):
            return SeverityResult("high", 1.0, "rainfall", mm_per_hour)
        elif mm_per_hour > 80:
            return SeverityResult("high", 1.0, "rainfall", mm_per_hour)
        elif mm_per_hour >= 65:
            return SeverityResult("moderate", 0.8, "rainfall", mm_per_hour)
        else:
            return SeverityResult("low", 0.0, "rainfall", mm_per_hour)

    def _score_heat(self, temp_celsius: float) -> SeverityResult:
        if temp_celsius >= 44:
            return SeverityResult("moderate", 0.85, "heat", temp_celsius)
        return SeverityResult("low", 0.0, "heat", temp_celsius)

    def _score_aqi(self, aqi: float) -> SeverityResult:
        if aqi > 450:
            return SeverityResult("high", 1.0, "aqi", aqi)
        elif aqi > 400:
            return SeverityResult("moderate", 0.85, "aqi", aqi)
        return SeverityResult("low", 0.0, "aqi", aqi)

    def _score_outage(self, minutes: float) -> SeverityResult:
        if minutes > 90:
            return SeverityResult("moderate", 0.9, "outage", minutes)
        elif minutes >= 45:
            return SeverityResult("low", 0.7, "outage", minutes)
        return SeverityResult("low", 0.0, "outage", minutes)
