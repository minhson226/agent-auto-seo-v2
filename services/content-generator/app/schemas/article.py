"""Schemas for Content Generator Service."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Article Schemas
class ArticleGenerateRequest(BaseModel):
    """Schema for generating an article from a content plan."""

    plan_id: UUID


class ArticleCreate(BaseModel):
    """Schema for creating an article directly."""

    workspace_id: UUID
    plan_id: Optional[UUID] = None
    title: str = Field(..., min_length=1, max_length=500)
    content: Optional[str] = None
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")
    ai_model_used: str = Field(default="gpt-3.5-turbo")
    word_count: Optional[int] = Field(None, ge=0)
    metadata: Optional[Dict[str, Any]] = None


class ArticleUpdate(BaseModel):
    """Schema for updating an article."""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$")
    metadata: Optional[Dict[str, Any]] = None


class ArticleImageResponse(BaseModel):
    """Schema for article image response."""

    id: UUID
    article_id: UUID
    filename: str
    original_filename: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    storage_path: str
    created_at: datetime

    class Config:
        from_attributes = True


class ArticleResponse(BaseModel):
    """Schema for article response."""

    id: UUID
    workspace_id: UUID
    plan_id: Optional[UUID] = None
    title: str
    content: Optional[str] = None
    status: str
    ai_model_used: str
    cost_usd: Optional[Decimal] = None
    word_count: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    images: List[ArticleImageResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    """Schema for article response in list (without content for performance)."""

    id: UUID
    workspace_id: UUID
    plan_id: Optional[UUID] = None
    title: str
    status: str
    ai_model_used: str
    cost_usd: Optional[Decimal] = None
    word_count: Optional[int] = None
    image_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedArticleResponse(BaseModel):
    """Schema for paginated article response."""

    data: List[ArticleListResponse]
    total: int
    page: int
    page_size: int


class GenerationResult(BaseModel):
    """Schema for content generation result."""

    content: str
    cost_usd: Decimal
    model: str
    word_count: int
    tokens_used: Dict[str, int]
