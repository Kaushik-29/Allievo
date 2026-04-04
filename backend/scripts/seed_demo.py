"""Seed script to initialize database with demo data."""
import os
import sys
import uuid
import datetime

# Add root backend dir to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, Base, engine
from app.models.worker import Worker
from app.models.zone_score import ZoneScore

def seed():
    # Make sure tables exist (usually Alembic does this, but for simple tests we can rely on create_all)
    # Base.metadata.create_all(bind=engine) # Assume alembic will be run first
    
    db: Session = SessionLocal()
    
    try:
        # Example Zones
        bengaluru_koramangala = ZoneScore(
            zone_name="Koramangala",
            city="Bengaluru",
            zone_boundary="POLYGON((77.610 12.925, 77.635 12.925, 77.635 12.945, 77.610 12.945, 77.610 12.925))",
            zone_type="low",
            disruption_days_yr=12,
            risk_multiplier=1.0,
            risk_score_current=0.35
        )
        
        mumbai_andheri = ZoneScore(
            zone_name="Andheri East",
            city="Mumbai",
            zone_boundary="POLYGON((72.860 19.110, 72.880 19.110, 72.880 19.125, 72.860 19.125, 72.860 19.110))",
            zone_type="flood",
            disruption_days_yr=25,
            risk_multiplier=1.45,
            risk_score_current=0.65
        )
        
        db.add_all([bengaluru_koramangala, mumbai_andheri])
        db.commit()
        db.refresh(bengaluru_koramangala)
        db.refresh(mumbai_andheri)
        print("Zones created.")
        
        # Example Worker
        worker_1 = Worker(
            phone="+919876543210",
            name="Ravi Kumar",
            city="Bengaluru",
            language_pref="kn",
            zomato_linked=True,
            swiggy_linked=False,
            is_active=True
        )
        
        db.add(worker_1)
        db.commit()
        db.refresh(worker_1)
        print(f"Worker created: {worker_1.id}")
        
        # Create a policy and some trigger event + claim for testing if needed
        # (Omitted to keep it simple, but you get the idea)
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting demo database seed...")
    seed()
    print("Done!")
