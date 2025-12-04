"""Schemas for SEO Scorer Service."""

from datetime import datetime
from typing import Any, Dict, List, Optional
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


# Auto-scoring schemas (PHASE-010)


class AutoScoreRequest(BaseModel):
    """Schema for auto-scoring request."""

    html_content: str = Field(..., description="HTML content to analyze")
    target_keywords: List[str] = Field(..., description="Target keywords to check for")
    article_id: Optional[UUID] = Field(None, description="Optional article ID")
    workspace_id: Optional[UUID] = Field(None, description="Optional workspace ID")


class HTMLAnalysisResult(BaseModel):
    """Schema for HTML analysis result."""

    title_contains_keyword: bool
    h1_present: bool
    h1_count: int
    h1_contains_keyword: bool
    h2_count: int
    h2_contains_keyword: bool
    keyword_density: float
    keyword_density_ok: bool
    images_count: int
    images_with_alt: int
    images_without_alt: int
    images_have_alt: bool
    word_count: int
    word_count_adequate: bool
    internal_links: int
    external_links: int
    has_internal_links: bool
    has_external_links: bool
    meta_description: bool
    meta_description_length: int
    title_length: int
    score: int


class ScoreBreakdownItem(BaseModel):
    """Schema for score breakdown item."""

    value: Any
    weight: int
    passed: bool
    points: int


class DetailedScoreResponse(BaseModel):
    """Schema for detailed auto score response."""

    score: int
    total_points: int
    max_points: int
    breakdown: Dict[str, ScoreBreakdownItem]
    status: str


class AutoScoreResponse(BaseModel):
    """Schema for auto-scoring response."""

    score: int
    status: str
    analysis: HTMLAnalysisResult
    detailed_score: DetailedScoreResponse
    issues: List[str] = []
    suggestions: List[Dict[str, str]] = []


class CorrectionRequest(BaseModel):
    """Schema for correction request."""

    article_id: str = Field(..., description="Article ID to correct")
    html_content: str = Field(..., description="HTML content to analyze")
    target_keywords: List[str] = Field(..., description="Target keywords")
    workspace_id: Optional[UUID] = Field(None, description="Workspace ID")
    correction_attempt: int = Field(0, ge=0, le=3, description="Current correction attempt")


class CorrectionResponse(BaseModel):
    """Schema for correction response."""

    action: str
    article_id: str
    score: int
    issues: List[str] = []
    correction_instructions: List[str] = []
    correction_attempt: int = 0
    message: str


class WeightAdjustmentRequest(BaseModel):
    """Schema for weight adjustment request."""

    workspace_id: UUID


class ArticlePerformanceData(BaseModel):
    """Schema for article performance data input."""

    seo_checklist_values: Dict[str, bool]
    avg_position: float


class WeightAdjustmentResponse(BaseModel):
    """Schema for weight adjustment response."""

    success: bool
    workspace_id: str
    reason: Optional[str] = None
    new_weights: Optional[Dict[str, int]] = None
    samples_used: Optional[int] = None
    model_accuracy: Optional[float] = None
