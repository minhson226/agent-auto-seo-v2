"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.topic_clusters import router as topic_clusters_router
from app.api.v1.content_plans import router as content_plans_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(topic_clusters_router)
api_router.include_router(content_plans_router)
