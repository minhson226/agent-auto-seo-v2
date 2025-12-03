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
