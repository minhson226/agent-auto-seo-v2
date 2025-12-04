"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.seo_scores import router as seo_scores_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(seo_scores_router)
