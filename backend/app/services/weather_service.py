import httpx
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class WeatherService:
    """
    Fetches real-time 7-day weather forecasting data using the free Open-Meteo API.
    Does not require API keys, heavily utilized for hacking/rapid prototyping.
    """
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    # Defaulting to active Bengaluru coordinates as specified in planning phase.
    DEFAULT_LAT = 12.9716
    DEFAULT_LNG = 77.5946

    def get_7d_risk_forecast(self, lat: float = DEFAULT_LAT, lng: float = DEFAULT_LNG) -> Dict[str, float]:
        """
        Pulls max precipitation probability and sum to construct Rain Risk properties.
        """
        params = {
            "latitude": lat,
            "longitude": lng,
            "daily": ["precipitation_probability_max", "precipitation_sum"],
            "timezone": "auto"
        }
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                
                daily = data.get("daily", {})
                probs = daily.get("precipitation_probability_max", [])
                sums = daily.get("precipitation_sum", [])
                
                if not probs or not sums:
                    return self._fallback_risk()
                
                # We calculate peak probability over the next 7 days
                peak_prob = max([p for p in probs if p is not None] or [0])
                
                # Determine severity factor based on total expected millimeter volume max across 7 days
                peak_sum = max([s for s in sums if s is not None] or [0])
                
                if peak_sum > 40:
                    severity = 1.0     # Severe alert!
                elif peak_sum > 15:
                    severity = 0.6     # Moderate rain constraint
                elif peak_sum > 0:
                    severity = 0.3     # Light to minimal drizzle risk
                else:
                    severity = 0.0     # Dry
                    
                return {
                    "rain_probability_7d": round((peak_prob / 100.0), 3),
                    "rain_severity_factor": severity
                }

        except Exception as e:
            logger.error(f"Failed to fetch forecast from Open-Meteo: {e}")
            return self._fallback_risk()

    def _fallback_risk(self) -> Dict[str, float]:
        """Graceful degradation in case API fails."""
        return {
            "rain_probability_7d": 0.4,
            "rain_severity_factor": 0.6
        }
