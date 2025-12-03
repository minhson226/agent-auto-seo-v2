"""API Key schemas."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ApiKeyBase(BaseModel):
    """Base API key schema."""

    service_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of the service (e.g., 'openai', 'google', 'ahrefs')",
    )
    settings: Optional[Dict[str, Any]] = None


class ApiKeyCreate(ApiKeyBase):
    """Schema for creating an API key."""

    api_key: str = Field(..., min_length=1, description="The API key value")


class ApiKeyResponse(ApiKeyBase):
    """Schema for API key response (does not include the actual key)."""

    id: UUID
    workspace_id: UUID
    created_at: datetime
    updated_at: datetime
    # Note: api_key is never returned in responses for security

    class Config:
        from_attributes = True


class ApiKeyWithValue(ApiKeyResponse):
    """Schema for API key with decrypted value (use sparingly)."""

    api_key: str  # Decrypted API key value
