"""Keyword and KeywordList schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class KeywordListCreate(BaseModel):
    """Schema for creating a keyword list."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    workspace_id: UUID


class KeywordListResponse(BaseModel):
    """Schema for keyword list response."""

    id: UUID
    workspace_id: UUID
    name: str
    description: Optional[str] = None
    source: Optional[str] = None
    source_file_url: Optional[str] = None
    total_keywords: int = 0
    status: str = "processing"
    error_message: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaginatedKeywordListResponse(BaseModel):
    """Schema for paginated keyword list response."""

    data: List[KeywordListResponse]
    total: int
    page: int
    page_size: int


class KeywordCreate(BaseModel):
    """Schema for creating a keyword."""

    text: str = Field(..., min_length=1, max_length=500)


class KeywordResponse(BaseModel):
    """Schema for keyword response."""

    id: UUID
    list_id: UUID
    text: str
    normalized_text: str
    status: str = "pending"
    intent: str = "unknown"
    search_volume: Optional[int] = None
    keyword_difficulty: Optional[Decimal] = None
    # PHASE-004: New enrichment fields
    cpc: Optional[Decimal] = None
    clicks: Optional[int] = None
    intent_confidence: Optional[Decimal] = None
    trend_score: Optional[int] = None
    last_enriched_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedKeywordResponse(BaseModel):
    """Schema for paginated keyword response."""

    data: List[KeywordResponse]
    total: int
    page: int
    page_size: int


class StatusCount(BaseModel):
    """Schema for status counts."""

    pending: int = 0
    processed: int = 0
    assigned: int = 0


class IntentCount(BaseModel):
    """Schema for intent counts."""

    unknown: int = 0
    informational: int = 0
    commercial: int = 0
    navigational: int = 0
    transactional: int = 0


class KeywordListStats(BaseModel):
    """Schema for keyword list statistics."""

    total: int
    by_status: StatusCount
    by_intent: IntentCount


# PHASE-004: New schemas for automation features

class EnrichKeywordsRequest(BaseModel):
    """Schema for enriching keywords request."""

    list_id: UUID
    source: str = Field(default="ahrefs", pattern="^(ahrefs|semrush)$")


class EnrichKeywordsResponse(BaseModel):
    """Schema for enriching keywords response."""

    list_id: UUID
    status: str = "processing"
    message: str = "Keyword enrichment started"
    task_id: Optional[str] = None


class TrendingKeywordsRequest(BaseModel):
    """Schema for fetching trending keywords."""

    workspace_id: UUID
    geo: str = Field(default="US", max_length=5)
    category: Optional[str] = None


class TrendingKeywordsResponse(BaseModel):
    """Schema for trending keywords response."""

    workspace_id: UUID
    list_id: Optional[UUID] = None
    status: str = "processing"
    message: str = "Trending keywords discovery started"
    task_id: Optional[str] = None


class CompetitorKeywordsRequest(BaseModel):
    """Schema for fetching competitor keywords."""

    workspace_id: UUID
    competitor_domain: str = Field(..., min_length=1, max_length=255)
    limit: int = Field(default=100, ge=1, le=1000)


class CompetitorKeywordsResponse(BaseModel):
    """Schema for competitor keywords response."""

    workspace_id: UUID
    competitor_domain: str
    list_id: Optional[UUID] = None
    status: str = "processing"
    message: str = "Competitor keywords analysis started"
    task_id: Optional[str] = None


class PasteKeywordsRequest(BaseModel):
    """Schema for pasting keywords directly."""

    workspace_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    keywords: List[str] = Field(..., min_length=1)
    description: Optional[str] = None


class PasteKeywordsResponse(BaseModel):
    """Schema for paste keywords response."""

    list_id: UUID
    name: str
    total_keywords: int
    status: str = "completed"
    message: str = "Keywords imported successfully"


class ClassifyIntentRequest(BaseModel):
    """Schema for intent classification request."""

    keyword: str = Field(..., min_length=1, max_length=500)


class ClassifyIntentResponse(BaseModel):
    """Schema for intent classification response."""

    keyword: str
    intent: str
    confidence: float = Field(..., ge=0, le=100)
    all_scores: Optional[Dict[str, float]] = None


class BatchClassifyIntentRequest(BaseModel):
    """Schema for batch intent classification."""

    keywords: List[str] = Field(..., min_length=1, max_length=100)


class BatchClassifyIntentResponse(BaseModel):
    """Schema for batch intent classification response."""

    results: List[ClassifyIntentResponse]
    total: int


class KeywordMetricsResponse(BaseModel):
    """Schema for keyword metrics from external sources."""

    keyword: str
    search_volume: int = 0
    keyword_difficulty: float = 0.0
    cpc: float = 0.0
    clicks: int = 0
    source: str


class RelatedKeywordsResponse(BaseModel):
    """Schema for related keywords response."""

    seed_keyword: str
    related: List[Dict[str, Any]]
    source: str
    total: int

