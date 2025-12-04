"""SEO Scores API endpoints."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.seo_score import (
    SeoScoreCreate,
    SeoScoreResponse,
    SeoScoreUpdate,
    PaginatedSeoScoreResponse,
    ScoreCalculationResponse,
)
from app.services.seo_score_service import SeoScoreService
from app.services.event_publisher import event_publisher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/seo-scores", tags=["SEO Scores"])


@router.post("", response_model=SeoScoreResponse, status_code=status.HTTP_201_CREATED)
async def create_seo_score(
    data: SeoScoreCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new SEO score entry.

    Creates an SEO score with a checklist. The manual score is
    automatically calculated based on the checklist items.
    """
    service = SeoScoreService(db)
    seo_score = await service.create(data)

    # Publish event
    try:
        await event_publisher.publish(
            "seo.score.created",
            {
                "score_id": seo_score.id,
                "article_id": seo_score.article_id,
                "workspace_id": seo_score.workspace_id,
                "manual_score": seo_score.manual_score,
                "status": seo_score.status,
            },
            workspace_id=seo_score.workspace_id,
        )
    except Exception as e:
        logger.warning(f"Failed to publish event: {e}")

    return SeoScoreResponse(
        id=seo_score.id,
        article_id=seo_score.article_id,
        workspace_id=seo_score.workspace_id,
        manual_score=seo_score.manual_score,
        auto_score=seo_score.auto_score,
        checklist=seo_score.checklist,
        status=seo_score.status,
        created_at=seo_score.created_at,
        updated_at=seo_score.updated_at,
    )


@router.get("", response_model=PaginatedSeoScoreResponse)
async def list_seo_scores(
    workspace_id: UUID,
    article_id: Optional[UUID] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List SEO scores for a workspace.

    Optionally filter by article_id or status (pending, completed, reviewed).
    """
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 1
    if page_size > 100:
        page_size = 100

    service = SeoScoreService(db)
    scores, total = await service.get_by_workspace(
        workspace_id=workspace_id,
        article_id=article_id,
        status=status,
        page=page,
        page_size=page_size,
    )

    data = []
    for score in scores:
        data.append(
            SeoScoreResponse(
                id=score.id,
                article_id=score.article_id,
                workspace_id=score.workspace_id,
                manual_score=score.manual_score,
                auto_score=score.auto_score,
                checklist=score.checklist,
                status=score.status,
                created_at=score.created_at,
                updated_at=score.updated_at,
            )
        )

    return PaginatedSeoScoreResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{score_id}", response_model=SeoScoreResponse)
async def get_seo_score(
    score_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific SEO score by ID."""
    service = SeoScoreService(db)
    score = await service.get_by_id(score_id)

    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SEO score not found",
        )

    return SeoScoreResponse(
        id=score.id,
        article_id=score.article_id,
        workspace_id=score.workspace_id,
        manual_score=score.manual_score,
        auto_score=score.auto_score,
        checklist=score.checklist,
        status=score.status,
        created_at=score.created_at,
        updated_at=score.updated_at,
    )


@router.put("/{score_id}", response_model=SeoScoreResponse)
async def update_seo_score(
    score_id: UUID,
    data: SeoScoreUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an SEO score.

    Updates the checklist and/or status. The manual score is
    automatically recalculated when the checklist is updated.
    """
    service = SeoScoreService(db)
    score = await service.update(score_id, data)

    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SEO score not found",
        )

    # Publish event
    try:
        await event_publisher.publish(
            "seo.score.updated",
            {
                "score_id": score.id,
                "article_id": score.article_id,
                "workspace_id": score.workspace_id,
                "manual_score": score.manual_score,
                "status": score.status,
            },
            workspace_id=score.workspace_id,
        )
    except Exception as e:
        logger.warning(f"Failed to publish event: {e}")

    return SeoScoreResponse(
        id=score.id,
        article_id=score.article_id,
        workspace_id=score.workspace_id,
        manual_score=score.manual_score,
        auto_score=score.auto_score,
        checklist=score.checklist,
        status=score.status,
        created_at=score.created_at,
        updated_at=score.updated_at,
    )


@router.delete("/{score_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_seo_score(
    score_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an SEO score."""
    service = SeoScoreService(db)
    deleted = await service.delete(score_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SEO score not found",
        )


@router.post("/calculate", response_model=ScoreCalculationResponse)
async def calculate_score(
    checklist: dict,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Calculate score from a checklist without saving.

    This endpoint is useful for previewing the score before saving.
    """
    result = SeoScoreService.calculate_score_from_checklist(checklist)
    return ScoreCalculationResponse(**result)
