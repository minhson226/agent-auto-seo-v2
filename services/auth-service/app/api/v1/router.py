"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.workspaces import router as workspaces_router
from app.api.v1.sites import router as sites_router
from app.api.v1.api_keys import router as api_keys_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(workspaces_router)
api_router.include_router(sites_router)
api_router.include_router(api_keys_router)
