"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.v1.analytics import router as analytics_router
from app.api.v1.strategic_learning import router as strategic_learning_router

api_router = APIRouter(prefix="/api/v1")

# Include sub-routers
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(
    strategic_learning_router, prefix="/strategic-learning", tags=["Strategic Learning"]
)
