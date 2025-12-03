"""Workspace schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class WorkspaceBase(BaseModel):
    """Base workspace schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class WorkspaceCreate(WorkspaceBase):
    """Schema for creating a workspace."""

    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")


class WorkspaceUpdate(BaseModel):
    """Schema for updating a workspace."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class WorkspaceResponse(WorkspaceBase):
    """Schema for workspace response."""

    id: UUID
    slug: str
    owner_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkspaceMemberCreate(BaseModel):
    """Schema for adding a workspace member."""

    user_id: UUID
    role: str = Field(default="member", pattern=r"^(admin|member|viewer)$")


class WorkspaceMemberResponse(BaseModel):
    """Schema for workspace member response."""

    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: str
    permissions: List[str]
    joined_at: datetime

    class Config:
        from_attributes = True
