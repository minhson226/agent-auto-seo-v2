"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.automation import router as automation_router
from app.api.v1.intent import router as intent_router
from app.api.v1.keyword_lists import router as keyword_lists_router
from app.api.v1.keywords import router as keywords_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(keyword_lists_router)
api_router.include_router(keywords_router)
api_router.include_router(automation_router)
api_router.include_router(intent_router)
