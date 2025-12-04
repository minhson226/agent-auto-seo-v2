"""Schemas for SEO Strategy Service."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Topic Cluster Schemas
class TopicClusterCreate(BaseModel):
    """Schema for creating a topic cluster."""

    workspace_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(default="cluster", pattern="^(pillar|cluster)$")
    description: Optional[str] = None
    pillar_cluster_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None


class TopicClusterUpdate(BaseModel):
    """Schema for updating a topic cluster."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = Field(None, pattern="^(pillar|cluster)$")
    description: Optional[str] = None
    pillar_cluster_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None


class TopicClusterResponse(BaseModel):
    """Schema for topic cluster response."""

    id: UUID
    workspace_id: UUID
    name: str
    type: str
    description: Optional[str] = None
    pillar_cluster_id: Optional[UUID] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    keyword_count: int = 0

    class Config:
        from_attributes = True


class PaginatedTopicClusterResponse(BaseModel):
    """Schema for paginated topic cluster response."""

    data: List[TopicClusterResponse]
    total: int
    page: int
    page_size: int


# Cluster Keyword Schemas
class ClusterKeywordAdd(BaseModel):
    """Schema for adding a keyword to a cluster."""

    keyword_id: UUID
    is_primary: bool = False


class ClusterKeywordBatchAdd(BaseModel):
    """Schema for adding multiple keywords to a cluster."""

    keyword_ids: List[UUID]
    is_primary: bool = False


class ClusterKeywordResponse(BaseModel):
    """Schema for cluster keyword response."""

    cluster_id: UUID
    keyword_id: UUID
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Content Plan Schemas
class ContentPlanCreate(BaseModel):
    """Schema for creating a content plan."""

    workspace_id: UUID
    cluster_id: Optional[UUID] = None
    title: str = Field(..., min_length=1, max_length=500)
    priority: str = Field(default="medium", pattern="^(high|medium|low)$")
    target_keywords: Optional[List[str]] = None
    competitors_data: Optional[Dict[str, Any]] = None
    status: str = Field(default="draft", pattern="^(draft|approved|in_progress|completed)$")
    estimated_word_count: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


class ContentPlanUpdate(BaseModel):
    """Schema for updating a content plan."""

    cluster_id: Optional[UUID] = None
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    priority: Optional[str] = Field(None, pattern="^(high|medium|low)$")
    target_keywords: Optional[List[str]] = None
    competitors_data: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, pattern="^(draft|approved|in_progress|completed)$")
    estimated_word_count: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None


class ContentPlanResponse(BaseModel):
    """Schema for content plan response."""

    id: UUID
    workspace_id: UUID
    cluster_id: Optional[UUID] = None
    title: str
    priority: str
    target_keywords: Optional[List[str]] = None
    competitors_data: Optional[Dict[str, Any]] = None
    status: str
    estimated_word_count: Optional[int] = None
    notes: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedContentPlanResponse(BaseModel):
    """Schema for paginated content plan response."""

    data: List[ContentPlanResponse]
    total: int
    page: int
    page_size: int
