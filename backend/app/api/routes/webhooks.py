"""Webhooks API — /api/v1/webhooks"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.models.payout import Payout

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Receive async payment confirmations from Razorpay."""
    payload = await request.json()
    
    # In production, verify Razorpay signature here using settings.RAZORPAY_WEBHOOK_SECRET
    
    event = payload.get("event")
    if event == "payout.processed":
        payout_data = payload.get("payload", {}).get("payout", {}).get("entity", {})
        transfer_id = payout_data.get("id")
        
        payout = db.query(Payout).filter(Payout.razorpay_transfer_id == transfer_id).first()
        if payout:
            payout.status = "success"
            payout.completed_at = __import__('datetime').datetime.utcnow()
            db.commit()
            logger.info(f"Razorpay Webhook: Payout {payout.id} processed successfully.")
            
    elif event in ["payout.failed", "payout.reversed"]:
        payout_data = payload.get("payload", {}).get("payout", {}).get("entity", {})
        transfer_id = payout_data.get("id")
        failure_reason = payout_data.get("failure_reason", "Unknown failure")
        
        payout = db.query(Payout).filter(Payout.razorpay_transfer_id == transfer_id).first()
        if payout:
            payout.status = "failed"
            payout.failure_reason = failure_reason
            db.commit()
            logger.error(f"Razorpay Webhook: Payout {payout.id} failed. Reason: {failure_reason}")
            
    return {"status": "ok"}


@router.post("/platform-status")
async def platform_status_webhook(
    payload: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Receive push notifications for Swiggy/Zomato outages."""
    platform = payload.get("platform")
    status = payload.get("status")
    duration = payload.get("duration", 0)
    
    if status == "outage" and duration >= 45:
        # Create a trigger event
        logger.info(f"Platform outage detected via webhook: {platform} for {duration} mins")
        # Actual trigger logic is handled by TriggerMonitor.
        # This endpoint could update a cache that the monitor reads from.
        
    return {"status": "received"}
