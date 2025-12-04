"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.articles import router as articles_router
from app.api.v1.llm import router as llm_router
from app.api.v1.images import router as images_router
from app.api.v1.scheduler import router as scheduler_router
from app.api.v1.rag import router as rag_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(articles_router)
api_router.include_router(llm_router)
api_router.include_router(images_router)
api_router.include_router(scheduler_router)
api_router.include_router(rag_router)
