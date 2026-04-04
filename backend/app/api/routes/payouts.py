from fastapi import APIRouter

router = APIRouter(prefix="/payouts", tags=["payouts"])

# Most payout logic is either in the payout_pipeline or 
# exposed via the /claims/{worker_id}/payout-status endpoint.
# Left empty or for future extensions.
