from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Allievo"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://allievo:allievo_dev@localhost:5432/allievo"
    DB_PASSWORD: str = "allievo_dev"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-this-to-a-secure-256-bit-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 days

    # External APIs
    OPENWEATHERMAP_API_KEY: str = "mock"
    IMD_API_KEY: str = "mock"
    CPCB_API_KEY: str = "mock"
    FINGERPRINTJS_API_KEY: str = "mock"

    # Razorpay
    RAZORPAY_KEY_ID: str = "rzp_test_mock"
    RAZORPAY_KEY_SECRET: str = "mock_secret"

    # SMS
    SMS_PROVIDER_API_KEY: str = "mock"
    SMS_SENDER_ID: str = "ALIEVO"
    SMS_PROVIDER: str = "msg91"

    # Platform OAuth
    ZOMATO_CLIENT_ID: str = "mock"
    ZOMATO_CLIENT_SECRET: str = "mock"
    SWIGGY_CLIENT_ID: str = "mock"
    SWIGGY_CLIENT_SECRET: str = "mock"

    # Encryption
    FIELD_ENCRYPTION_KEY: str = "change-this-to-a-32-byte-fernet-key"

    # Webhooks
    ADMIN_WEBHOOK_URL: str = "http://localhost:8000/internal/review-queue"

    # ——————————————————————————————————————————————
    # HARDCODED BUSINESS RULES (Section 10) — NEVER CHANGE
    # ——————————————————————————————————————————————

    # Premium engine
    BASE_RATE: float = 40.0
    DYNAMIC_AMPLIFIER: float = 0.75
    PREMIUM_CAP: float = 100.0
    PREMIUM_FLOOR: float = 30.0
    LOYALTY_ADJUSTMENT_WEEK_5_12: float = 0.95
    LOYALTY_ADJUSTMENT_WEEK_13_PLUS: float = 0.90
    
    # Dynamic Pricing (Section 4.2 Update)
    WEATHER_SURGE_THRESHOLD: float = 0.60
    WEATHER_SURGE_AMPLIFIER: float = 1.25

    # Tier definitions
    TIER_BASIC_MAX_PAYOUT: int = 400
    TIER_STANDARD_MAX_PAYOUT: int = 700
    TIER_PREMIUM_MAX_PAYOUT: int = 1000
    TIER_BASIC_COVERAGE_HOURS: int = 4
    TIER_STANDARD_COVERAGE_HOURS: int = 6
    TIER_PREMIUM_COVERAGE_HOURS: int = 8
    TIER_BASIC_COVERAGE_FACTOR: float = 0.7
    TIER_STANDARD_COVERAGE_FACTOR: float = 1.0
    TIER_PREMIUM_COVERAGE_FACTOR: float = 1.3

    # Waiting period
    WAITING_PERIOD_WEEKS: int = 4

    # DAE caps
    DAE_HARD_CAP: float = 2000.0
    COLD_START_THRESHOLD_DAYS: int = 30
    DAE_REFRESH_DAYS: int = 30

    # Fraud gate
    MANDATORY_GATE_SECONDS: int = 300
    FRAUD_AUTO_APPROVE_MAX: float = 0.30
    FRAUD_PARTIAL_MAX: float = 0.55
    FRAUD_HOLD_MAX: float = 0.70
    PARTIAL_PAY_FIRST_PCT: float = 60.0
    PARTIAL_HOLD_PCT: float = 40.0
    PARTIAL_RELEASE_HOURS: int = 24
    RECONCILIATION_INTERVAL_HOURS: int = 6
    OVERDUE_ESCALATION_HOURS: int = 26
    FALSE_POSITIVE_BASELINE_ADJUST: float = 0.08
    FALSE_POSITIVE_WINDOW_DAYS: int = 90
    FALSE_POSITIVE_COUNT_THRESHOLD: int = 2

    # Zone presence
    ZONE_PRESENCE_HIGH_SUSPICION: float = 0.10
    ZONE_PRESENCE_CREDIBILITY: float = 0.50
    ZONE_PRESENCE_MIN_PINGS_PER_DAY: int = 1

    # GPS
    CELL_TOWER_MISMATCH_THRESHOLD_METERS: float = 500
    GPS_TRAJECTORY_LOOKBACK_MINUTES: int = 90
    GPS_SIGNAL_GAP_GRACE_MINUTES: int = 45
    GPS_RETENTION_DAYS: int = 90

    # Ring detection
    RING_ALERT_MIN_SIGNALS: int = 3
    RING_TEMPORAL_BURST_WINDOW_MINUTES: int = 3
    RING_TEMPORAL_BURST_MIN_CLAIMS: int = 5
    RING_REFERRAL_CHAIN_THRESHOLD: int = 8
    RING_GPS_PROXIMITY_THRESHOLD_METERS: float = 10
    RING_GPS_PROXIMITY_MIN_ACCOUNTS: int = 10
    DEVICE_SHARE_LOOKBACK_DAYS: int = 30
    UPI_NEW_REGISTRATION_HOURS: int = 48

    # Trigger thresholds
    RAINFALL_TRIGGER_MM_PER_HOUR: float = 65
    RAINFALL_MODERATE_MAX: float = 80
    HEAT_TRIGGER_CELSIUS: float = 44
    AQI_TRIGGER_THRESHOLD: float = 400
    AQI_MODERATE_MAX: float = 450
    AQI_SUSTAINED_HOURS: int = 4
    OUTAGE_MIN_MINUTES: int = 45
    OUTAGE_MODERATE_MAX: int = 90
    CURFEW_ORDER_DROP_PCT: float = 80
    RAINFALL_ORDER_DROP_PCT: float = 30
    OUTAGE_ORDER_DROP_PCT: float = 30
    ORDER_DROP_WINDOW_MINUTES: int = 60
    ORDER_DROP_LOOKBACK_DAYS: int = 7
    OUTAGE_MIN_SOURCES: int = 2

    # Loss ratio
    LOSS_RATIO_TARGET_MIN: float = 60.0
    LOSS_RATIO_TARGET_MAX: float = 70.0
    LOSS_RATIO_REVIEW_THRESHOLD: float = 75.0
    LOSS_RATIO_IRDAI_THRESHOLD: float = 85.0
    LOSS_RATIO_CRISIS_THRESHOLD: float = 100.0

    # Reinsurance
    REINSURANCE_QUOTA_SHARE_PCT: float = 40.0
    REINSURANCE_STOP_LOSS_TRIGGER: int = 5_000_000
    REINSURANCE_STOP_LOSS_COVERAGE_PCT: float = 90.0
    PER_EVENT_AGGREGATE_CAP_MULTIPLIER: float = 1.5
    SOLVENCY_MARGIN_MULTIPLIER: float = 3.0

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
