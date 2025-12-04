"""Schemas for SEO Scorer Service."""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.core.constants import DEFAULT_CHECKLIST


class SeoScoreCreate(BaseModel):
    """Schema for creating an SEO score."""

    article_id: Optional[UUID] = None
    workspace_id: UUID
    checklist: Optional[Dict[str, bool]] = Field(default_factory=lambda: DEFAULT_CHECKLIST.copy())
    status: str = Field(default="pending", pattern="^(pending|completed|reviewed)$")

    @field_validator("checklist")
    @classmethod
    def validate_checklist(cls, v):
        if v is None:
            return DEFAULT_CHECKLIST.copy()
        # Ensure all values are boolean
        for key, value in v.items():
            if not isinstance(value, bool):
                raise ValueError(f"Checklist item '{key}' must be a boolean")
        return v


class SeoScoreUpdate(BaseModel):
    """Schema for updating an SEO score."""

    article_id: Optional[UUID] = None
    checklist: Optional[Dict[str, bool]] = None
    status: Optional[str] = Field(None, pattern="^(pending|completed|reviewed)$")

    @field_validator("checklist")
    @classmethod
    def validate_checklist(cls, v):
        if v is None:
            return None
        # Ensure all values are boolean
        for key, value in v.items():
            if not isinstance(value, bool):
                raise ValueError(f"Checklist item '{key}' must be a boolean")
        return v


class SeoScoreResponse(BaseModel):
    """Schema for SEO score response."""

    model_config = {"from_attributes": True}

    id: UUID
    article_id: Optional[UUID] = None
    workspace_id: UUID
    manual_score: Optional[int] = None
    auto_score: Optional[int] = None
    checklist: Dict[str, bool]
    status: str
    created_at: datetime
    updated_at: datetime


class PaginatedSeoScoreResponse(BaseModel):
    """Schema for paginated SEO score response."""

    data: List[SeoScoreResponse]
    total: int
    page: int
    page_size: int


class ScoreCalculationResponse(BaseModel):
    """Schema for score calculation response."""

    score: int
    total_items: int
    checked_items: int
    checklist: Dict[str, bool]
