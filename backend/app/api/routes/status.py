from fastapi import APIRouter, Depends
from app.services.weather_service import WeatherService
from app.services.curfew_service import CurfewService

router = APIRouter(prefix="/status", tags=["status"])
ws = WeatherService()
cs = CurfewService()

@router.get("/risk/{city}")
def get_zone_status(city: str = "Bengaluru"):
    """
    Returns real-time risk metrics for a specific city.
    Used by the Worker Dashboard for HUD and Alerts.
    """
    weather = ws.get_7d_risk_forecast()
    curfew = cs.check_curfew(city)
    
    return {
        "city": city,
        "weather": {
            "rain_probability": weather.get("rain_probability_7d", 0),
            "severity": weather.get("rain_severity_factor", 0),
            "temp": 28, # Placeholder for now, could be dynamic
            "aqi": 110  # Placeholder 
        },
        "civil_risk": {
            "active": curfew["curfew_active"],
            "event": curfew["news"],
            "source": curfew["source"],
            "url": curfew["link"]
        }
    }
