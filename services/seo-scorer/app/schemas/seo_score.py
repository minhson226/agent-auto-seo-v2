"""Schemas for SEO Scorer Service."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# Default SEO checklist structure
DEFAULT_CHECKLIST = {
    "title_contains_keyword": False,
    "h1_present": False,
    "h2_count_adequate": False,
    "keyword_density_ok": False,
    "images_have_alt": False,
    "meta_description": False,
    "internal_links": False,
    "external_links": False,
    "word_count_adequate": False,
    "readability_ok": False,
}


class ChecklistItem(BaseModel):
    """Individual checklist item."""

    title_contains_keyword: bool = False
    h1_present: bool = False
    h2_count_adequate: bool = False
    keyword_density_ok: bool = False
    images_have_alt: bool = False
    meta_description: bool = False
    internal_links: bool = False
    external_links: bool = False
    word_count_adequate: bool = False
    readability_ok: bool = False


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
