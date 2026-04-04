from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random

from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.worker import Worker
import redis
import json
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])

# Initializing Stateless Redis Cache pool
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

class WorkerRegister(BaseModel):
    username: str
    password: str
    name: str
    phone: str
    email: str
    city: str
    aadhar_no: str
    pan_no: str
    primary_platform: str # 'zomato' | 'swiggy'
    work_location: str
    current_location: str
    working_proof: Optional[str] = None

class WorkerLogin(BaseModel):
    username: str
    password: str

@router.post("/register")
def register_worker(data: WorkerRegister, db: Session = Depends(get_db)):
    # Check if username or phone already exists
    existing_user = db.query(Worker).filter(
        (Worker.username == data.username) | (Worker.phone == data.phone)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or Phone already registered")
    
    new_worker = Worker(
        username=data.username,
        hashed_password=get_password_hash(data.password),
        name=data.name,
        phone=data.phone,
        email=data.email,
        city=data.city,
        aadhar_no=data.aadhar_no,
        pan_no=data.pan_no,
        primary_platform=data.primary_platform,
        work_location=data.work_location,
        current_location=data.current_location,
        working_proof=data.working_proof,
        onboarded_at=datetime.utcnow()
    )
    
    db.add(new_worker)
    db.commit()
    db.refresh(new_worker)
    
    token = create_access_token({"sub": str(new_worker.id), "phone": new_worker.phone, "role": "worker"})
    
    return {
        "worker_id": str(new_worker.id),
        "access_token": token,
        "token_type": "bearer",
        "worker": {
            "name": new_worker.name,
            "username": new_worker.username
        }
    }

@router.post("/login")
def login_worker(data: WorkerLogin, db: Session = Depends(get_db)):
    worker = db.query(Worker).filter(Worker.username == data.username).first()
    
    if not worker or not verify_password(data.password, worker.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = create_access_token({"sub": str(worker.id), "phone": worker.phone, "role": "worker"})
    
    return {
        "worker_id": str(worker.id),
        "access_token": token,
        "token_type": "bearer",
        "worker": {
            "name": worker.name,
            "username": worker.username,
            "city": worker.city
        }
    }
