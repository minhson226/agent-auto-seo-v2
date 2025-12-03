"""Schemas module for Auth Service."""

from app.schemas.user import UserCreate, UserResponse, UserUpdate, UserInDB
from app.schemas.auth import Token, TokenPayload, LoginRequest, RefreshTokenRequest
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate, WorkspaceMemberCreate, WorkspaceMemberResponse
from app.schemas.site import SiteCreate, SiteResponse, SiteUpdate
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse

__all__ = [
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "UserInDB",
    "Token",
    "TokenPayload",
    "LoginRequest",
    "RefreshTokenRequest",
    "WorkspaceCreate",
    "WorkspaceResponse",
    "WorkspaceUpdate",
    "WorkspaceMemberCreate",
    "WorkspaceMemberResponse",
    "SiteCreate",
    "SiteResponse",
    "SiteUpdate",
    "ApiKeyCreate",
    "ApiKeyResponse",
]
