import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Text, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class Worker(Base):
    __tablename__ = "workers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=True)  # Nullable for existing legacy records migration
    hashed_password = Column(String(255), nullable=True)
    phone = Column(String(100), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    name = Column(String(100), nullable=False)
    
    # KYC & Profile
    aadhar_no = Column(String(20), nullable=True)
    pan_no = Column(String(20), nullable=True)
    primary_platform = Column(String(20), nullable=True) # 'zomato' | 'swiggy'
    work_location = Column(String(100), nullable=True)
    current_location = Column(String(100), nullable=True)
    working_proof = Column(Text, nullable=True)
    upi_id = Column(String(100), nullable=True)

    # Geolocation — registered work zone coordinates (set at registration)
    registered_lat = Column(Numeric(10, 7), nullable=True)   # e.g. 17.4647
    registered_lon = Column(Numeric(10, 7), nullable=True)   # e.g. 78.3513
    geofence_radius_km = Column(Numeric(5, 1), default=15.0) # 15km radius

    city = Column(String(50), nullable=False)
    language_pref = Column(String(10), default="en")
    zomato_linked = Column(Boolean, default=False)
    swiggy_linked = Column(Boolean, default=False)
    zomato_token = Column(Text, nullable=True)       # encrypted OAuth token
    swiggy_token = Column(Text, nullable=True)       # encrypted OAuth token
    onboarded_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    dpdp_consent_at = Column(DateTime(timezone=True), nullable=True)
    dpdp_consent_scope = Column(JSONB, nullable=True)  # {gps: true, device: true, platform: true}
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    device_fingerprints = relationship("DeviceFingerprint", back_populates="worker", cascade="all, delete-orphan")
    earnings_snapshots = relationship("EarningsSnapshot", back_populates="worker", cascade="all, delete-orphan")
    policies = relationship("Policy", back_populates="worker", cascade="all, delete-orphan")
    gps_pings = relationship("GpsPing", back_populates="worker", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="worker")
    fraud_scores = relationship("FraudScore", back_populates="worker")
    payouts = relationship("Payout", back_populates="worker")
    upi_entries = relationship("UpiGraph", back_populates="worker")
    worker_plans = relationship("WorkerPlan", back_populates="worker", cascade="all, delete-orphan")
    manual_claims = relationship("ManualClaim", back_populates="worker", cascade="all, delete-orphan")
