"""Content plans API endpoints."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.seo_strategy import (
    ContentPlanCreate,
    ContentPlanResponse,
    ContentPlanUpdate,
    PaginatedContentPlanResponse,
)
from app.services.content_plan_service import ContentPlanService
from app.services.event_publisher import event_publisher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content-plans", tags=["Content Plans"])


@router.post("", response_model=ContentPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_content_plan(
    data: ContentPlanCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new content plan.

    Content plans represent planned content pieces with priorities,
    target keywords, and competitor analysis data.
    """
    service = ContentPlanService(db)
    content_plan = await service.create(data, user_id=current_user.id)

    # Publish event
    try:
        await event_publisher.publish(
            "content.plan.created",
            {
                "plan_id": content_plan.id,
                "workspace_id": content_plan.workspace_id,
                "title": content_plan.title,
                "priority": content_plan.priority,
                "status": content_plan.status,
                "cluster_id": content_plan.cluster_id,
                "created_by": content_plan.created_by,
            },
            workspace_id=content_plan.workspace_id,
        )
    except Exception as e:
        logger.warning(f"Failed to publish event: {e}")

    return ContentPlanResponse(
        id=content_plan.id,
        workspace_id=content_plan.workspace_id,
        cluster_id=content_plan.cluster_id,
        title=content_plan.title,
        priority=content_plan.priority,
        target_keywords=content_plan.target_keywords,
        competitors_data=content_plan.competitors_data,
        status=content_plan.status,
        estimated_word_count=content_plan.estimated_word_count,
        notes=content_plan.notes,
        created_by=content_plan.created_by,
        created_at=content_plan.created_at,
        updated_at=content_plan.updated_at,
    )


@router.get("", response_model=PaginatedContentPlanResponse)
async def list_content_plans(
    workspace_id: UUID,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    cluster_id: Optional[UUID] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List content plans for a workspace.

    Optionally filter by status (draft, approved, in_progress, completed),
    priority (high, medium, low), or cluster_id.
    """
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 1
    if page_size > 100:
        page_size = 100

    service = ContentPlanService(db)
    plans, total = await service.get_by_workspace(
        workspace_id=workspace_id,
        status=status,
        priority=priority,
        cluster_id=cluster_id,
        page=page,
        page_size=page_size,
    )

    data = []
    for plan in plans:
        data.append(
            ContentPlanResponse(
                id=plan.id,
                workspace_id=plan.workspace_id,
                cluster_id=plan.cluster_id,
                title=plan.title,
                priority=plan.priority,
                target_keywords=plan.target_keywords,
                competitors_data=plan.competitors_data,
                status=plan.status,
                estimated_word_count=plan.estimated_word_count,
                notes=plan.notes,
                created_by=plan.created_by,
                created_at=plan.created_at,
                updated_at=plan.updated_at,
            )
        )

    return PaginatedContentPlanResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{plan_id}", response_model=ContentPlanResponse)
async def get_content_plan(
    plan_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific content plan."""
    service = ContentPlanService(db)
    plan = await service.get_by_id(plan_id)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content plan not found",
        )

    return ContentPlanResponse(
        id=plan.id,
        workspace_id=plan.workspace_id,
        cluster_id=plan.cluster_id,
        title=plan.title,
        priority=plan.priority,
        target_keywords=plan.target_keywords,
        competitors_data=plan.competitors_data,
        status=plan.status,
        estimated_word_count=plan.estimated_word_count,
        notes=plan.notes,
        created_by=plan.created_by,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.put("/{plan_id}", response_model=ContentPlanResponse)
async def update_content_plan(
    plan_id: UUID,
    data: ContentPlanUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a content plan."""
    service = ContentPlanService(db)
    plan = await service.update(plan_id, data)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content plan not found",
        )

    return ContentPlanResponse(
        id=plan.id,
        workspace_id=plan.workspace_id,
        cluster_id=plan.cluster_id,
        title=plan.title,
        priority=plan.priority,
        target_keywords=plan.target_keywords,
        competitors_data=plan.competitors_data,
        status=plan.status,
        estimated_word_count=plan.estimated_word_count,
        notes=plan.notes,
        created_by=plan.created_by,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content_plan(
    plan_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a content plan."""
    service = ContentPlanService(db)
    deleted = await service.delete(plan_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content plan not found",
        )
