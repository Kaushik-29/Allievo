"""
ManualClaim — worker-filed claim with reason, proof, and admin review.
Separate from the auto-generated Claim model which is triggered by sensors.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Numeric, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class ManualClaim(Base):
    __tablename__ = "manual_claims"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id       = Column(UUID(as_uuid=True), ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True)

    # What happened
    disruption_type = Column(String(30), nullable=False)    # rainfall | heat | aqi | curfew | outage | other
    disruption_date = Column(DateTime(timezone=True), nullable=False)
    disruption_hours = Column(Numeric(4, 1), nullable=False)# how many hours lost
    description     = Column(Text, nullable=False)          # worker's explanation

    # Proof submitted
    proof_url       = Column(Text, nullable=True)           # future: file upload URL
    proof_text      = Column(Text, nullable=True)           # screenshot description / text proof
    proof_type      = Column(String(30), nullable=True)     # screenshot | order_history | media | other

    # Worker's location at time of claim
    worker_lat      = Column(Numeric(10, 7), nullable=True)
    worker_lon      = Column(Numeric(10, 7), nullable=True)
    worker_registered_lat = Column(Numeric(10, 7), nullable=True)
    worker_registered_lon = Column(Numeric(10, 7), nullable=True)
    distance_from_zone_km = Column(Numeric(8, 3), nullable=True)  # computed at submission
    within_15km_radius = Column(Boolean, nullable=True)     # True if within geofence

    # Was working check
    declared_was_working = Column(Boolean, default=True)    # worker self-declaration
    platform_session_confirmed = Column(Boolean, nullable=True)  # checked via MockPlatformAPI

    # Payout estimate
    plan_name       = Column(String(20), nullable=True)
    hourly_rate     = Column(Numeric(8, 2), default=80.0)
    estimated_payout = Column(Numeric(10, 2), nullable=True)

    # Auto-verification result
    auto_score      = Column(Numeric(5, 3), nullable=True)  # 0.0–1.0 confidence score
    auto_result     = Column(String(20), nullable=True)     # auto_approve | review | auto_deny
    auto_checks     = Column(JSONB, nullable=True)          # {gps: True, platform: True, weather: True, ...}
    auto_reason     = Column(Text, nullable=True)           # plain-language result

    # Admin decision
    status          = Column(String(20), default="pending") # pending | auto_approved | under_review | approved | denied
    admin_id        = Column(String(100), nullable=True)    # who reviewed
    admin_note      = Column(Text, nullable=True)
    reviewed_at     = Column(DateTime(timezone=True), nullable=True)
    payout_amount   = Column(Numeric(10, 2), nullable=True) # final approved amount

    # Timestamps
    submitted_at    = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at      = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    worker = relationship("Worker", back_populates="manual_claims")

    def to_dict(self) -> dict:
        return {
            "id":               str(self.id),
            "worker_id":        str(self.worker_id),
            "disruption_type":  self.disruption_type,
            "disruption_date":  self.disruption_date.isoformat() if self.disruption_date else None,
            "disruption_hours": float(self.disruption_hours) if self.disruption_hours else 0,
            "description":      self.description,
            "proof_text":       self.proof_text,
            "proof_type":       self.proof_type,
            "within_15km_radius": self.within_15km_radius,
            "distance_from_zone_km": float(self.distance_from_zone_km) if self.distance_from_zone_km else None,
            "declared_was_working": self.declared_was_working,
            "plan_name":        self.plan_name,
            "estimated_payout": float(self.estimated_payout) if self.estimated_payout else None,
            "auto_score":       float(self.auto_score) if self.auto_score else None,
            "auto_result":      self.auto_result,
            "auto_checks":      self.auto_checks,
            "auto_reason":      self.auto_reason,
            "status":           self.status,
            "admin_note":       self.admin_note,
            "payout_amount":    float(self.payout_amount) if self.payout_amount else None,
            "submitted_at":     self.submitted_at.isoformat() if self.submitted_at else None,
            "reviewed_at":      self.reviewed_at.isoformat() if self.reviewed_at else None,
        }
