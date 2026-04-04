import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import workers, policies, claims, admin, webhooks, auth, status, plans, manual_claims

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Allievo Parametric Income Insurance API Phase 1",
)

# Set up CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Resouces
app.include_router(workers.router, prefix=settings.API_V1_STR)
app.include_router(policies.router, prefix=settings.API_V1_STR)
app.include_router(claims.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(status.router, prefix=settings.API_V1_STR)
app.include_router(webhooks.router, prefix=settings.API_V1_STR)
app.include_router(plans.router, prefix=settings.API_V1_STR)
app.include_router(manual_claims.router, prefix=settings.API_V1_STR)

@app.get("/healthz", tags=["system"])
def health_check():
    """System health check endpoint."""
    return {"status": "ok", "environment": settings.ENVIRONMENT}

@app.on_event("startup")
def on_startup():
    logger.info("Allievo Backend Starting Up...")
    if settings.ENVIRONMENT == "development":
        # In dev, we can preload model artifacts or connect to test DBs
        logger.info("Running in Development Mode")
        
@app.on_event("shutdown")
def on_shutdown():
    logger.info("Allievo Backend Shutting Down...")
