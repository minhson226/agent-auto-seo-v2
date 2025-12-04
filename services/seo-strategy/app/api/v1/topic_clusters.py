"""Topic clusters API endpoints."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.seo_strategy import (
    ClusterKeywordAdd,
    ClusterKeywordBatchAdd,
    ClusterKeywordResponse,
    PaginatedTopicClusterResponse,
    TopicClusterCreate,
    TopicClusterResponse,
    TopicClusterUpdate,
)
from app.services.topic_cluster_service import TopicClusterService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/topic-clusters", tags=["Topic Clusters"])


@router.post("", response_model=TopicClusterResponse, status_code=status.HTTP_201_CREATED)
async def create_topic_cluster(
    data: TopicClusterCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new topic cluster.

    Creates a topic cluster that can be either a 'pillar' (main topic) or
    a 'cluster' (supporting topic that links to a pillar).
    """
    service = TopicClusterService(db)
    cluster = await service.create(data)

    # Get keyword count
    keyword_count = await service.get_keyword_count(cluster.id)

    response = TopicClusterResponse(
        id=cluster.id,
        workspace_id=cluster.workspace_id,
        name=cluster.name,
        type=cluster.type,
        description=cluster.description,
        pillar_cluster_id=cluster.pillar_cluster_id,
        metadata=cluster.metadata_,
        created_at=cluster.created_at,
        updated_at=cluster.updated_at,
        keyword_count=keyword_count,
    )
    return response


@router.get("", response_model=PaginatedTopicClusterResponse)
async def list_topic_clusters(
    workspace_id: UUID,
    type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List topic clusters for a workspace.

    Optionally filter by type (pillar or cluster).
    """
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 1
    if page_size > 100:
        page_size = 100

    service = TopicClusterService(db)
    clusters, total = await service.get_by_workspace(
        workspace_id=workspace_id,
        cluster_type=type,
        page=page,
        page_size=page_size,
    )

    data = []
    for cluster in clusters:
        keyword_count = await service.get_keyword_count(cluster.id)
        data.append(
            TopicClusterResponse(
                id=cluster.id,
                workspace_id=cluster.workspace_id,
                name=cluster.name,
                type=cluster.type,
                description=cluster.description,
                pillar_cluster_id=cluster.pillar_cluster_id,
                metadata=cluster.metadata_,
                created_at=cluster.created_at,
                updated_at=cluster.updated_at,
                keyword_count=keyword_count,
            )
        )

    return PaginatedTopicClusterResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{cluster_id}", response_model=TopicClusterResponse)
async def get_topic_cluster(
    cluster_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific topic cluster."""
    service = TopicClusterService(db)
    cluster = await service.get_by_id(cluster_id)

    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic cluster not found",
        )

    keyword_count = await service.get_keyword_count(cluster.id)

    return TopicClusterResponse(
        id=cluster.id,
        workspace_id=cluster.workspace_id,
        name=cluster.name,
        type=cluster.type,
        description=cluster.description,
        pillar_cluster_id=cluster.pillar_cluster_id,
        metadata=cluster.metadata_,
        created_at=cluster.created_at,
        updated_at=cluster.updated_at,
        keyword_count=keyword_count,
    )


@router.put("/{cluster_id}", response_model=TopicClusterResponse)
async def update_topic_cluster(
    cluster_id: UUID,
    data: TopicClusterUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a topic cluster."""
    service = TopicClusterService(db)
    cluster = await service.update(cluster_id, data)

    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic cluster not found",
        )

    keyword_count = await service.get_keyword_count(cluster.id)

    return TopicClusterResponse(
        id=cluster.id,
        workspace_id=cluster.workspace_id,
        name=cluster.name,
        type=cluster.type,
        description=cluster.description,
        pillar_cluster_id=cluster.pillar_cluster_id,
        metadata=cluster.metadata_,
        created_at=cluster.created_at,
        updated_at=cluster.updated_at,
        keyword_count=keyword_count,
    )


@router.delete("/{cluster_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic_cluster(
    cluster_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a topic cluster."""
    service = TopicClusterService(db)
    deleted = await service.delete(cluster_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic cluster not found",
        )


@router.post(
    "/{cluster_id}/keywords",
    response_model=ClusterKeywordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_keyword_to_cluster(
    cluster_id: UUID,
    data: ClusterKeywordAdd,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a keyword to a topic cluster.

    This is used when users drag keywords into clusters via the UI.
    """
    service = TopicClusterService(db)
    cluster_keyword = await service.add_keyword(
        cluster_id=cluster_id,
        keyword_id=data.keyword_id,
        is_primary=data.is_primary,
    )

    if not cluster_keyword:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add keyword. Cluster not found or keyword already exists.",
        )

    return ClusterKeywordResponse.model_validate(cluster_keyword)


@router.post(
    "/{cluster_id}/keywords/batch",
    response_model=list[ClusterKeywordResponse],
    status_code=status.HTTP_201_CREATED,
)
async def add_keywords_batch_to_cluster(
    cluster_id: UUID,
    data: ClusterKeywordBatchAdd,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add multiple keywords to a topic cluster.

    This is used for batch operations when users select multiple keywords.
    """
    service = TopicClusterService(db)
    cluster_keywords = await service.add_keywords_batch(
        cluster_id=cluster_id,
        keyword_ids=data.keyword_ids,
        is_primary=data.is_primary,
    )

    if not cluster_keywords:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to add keywords. Cluster not found or all keywords already exist.",
        )

    return [ClusterKeywordResponse.model_validate(ck) for ck in cluster_keywords]


@router.delete(
    "/{cluster_id}/keywords/{keyword_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_keyword_from_cluster(
    cluster_id: UUID,
    keyword_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a keyword from a topic cluster."""
    service = TopicClusterService(db)
    removed = await service.remove_keyword(cluster_id, keyword_id)

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword not found in cluster",
        )


@router.get(
    "/{cluster_id}/keywords",
    response_model=list[ClusterKeywordResponse],
)
async def list_cluster_keywords(
    cluster_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all keywords in a topic cluster."""
    service = TopicClusterService(db)

    # Check if cluster exists
    cluster = await service.get_by_id(cluster_id)
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Topic cluster not found",
        )

    keywords = await service.get_cluster_keywords(cluster_id)
    return [ClusterKeywordResponse.model_validate(ck) for ck in keywords]
