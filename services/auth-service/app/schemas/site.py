"""Site schemas."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class SiteBase(BaseModel):
    """Base site schema."""

    name: str = Field(..., min_length=1, max_length=255)
    domain: str = Field(..., min_length=1, max_length=255)
    platform: str = Field(default="wordpress", pattern=r"^(wordpress|ghost|custom)$")
    settings: Optional[Dict[str, Any]] = None


class SiteCreate(SiteBase):
    """Schema for creating a site."""

    wp_api_endpoint: Optional[str] = None
    wp_auth_type: Optional[str] = Field(
        None, pattern=r"^(application_password|jwt)$"
    )
    wp_credentials: Optional[Dict[str, str]] = None  # Will be encrypted before storage


class SiteUpdate(BaseModel):
    """Schema for updating a site."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = None
    platform: Optional[str] = Field(None, pattern=r"^(wordpress|ghost|custom)$")
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    wp_api_endpoint: Optional[str] = None
    wp_auth_type: Optional[str] = Field(
        None, pattern=r"^(application_password|jwt)$"
    )
    wp_credentials: Optional[Dict[str, str]] = None


class SiteResponse(SiteBase):
    """Schema for site response."""

    id: UUID
    workspace_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_sync_at: Optional[datetime] = None

    class Config:
        from_attributes = True
