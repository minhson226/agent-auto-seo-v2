"""Keywords API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.keyword import KeywordResponse, PaginatedKeywordResponse
from app.services.keyword_list_service import KeywordListService

router = APIRouter(prefix="/keyword-lists/{list_id}/keywords", tags=["Keywords"])


@router.get("", response_model=PaginatedKeywordResponse)
async def list_keywords(
    list_id: UUID,
    status_filter: Optional[str] = None,
    intent: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List keywords from a keyword list with pagination."""
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 1
    if page_size > 100:
        page_size = 100

    service = KeywordListService(db)

    # Check if list exists
    keyword_list = await service.get_by_id(list_id)
    if not keyword_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword list not found",
        )

    keywords, total = await service.get_keywords(
        list_id=list_id,
        status=status_filter,
        intent=intent,
        page=page,
        page_size=page_size,
    )

    return PaginatedKeywordResponse(
        data=[
            KeywordResponse(
                id=kw.id,
                list_id=kw.list_id,
                text=kw.text,
                normalized_text=kw.normalized_text,
                status=kw.status,
                intent=kw.intent,
                search_volume=kw.search_volume,
                keyword_difficulty=kw.keyword_difficulty,
                metadata=kw.metadata_,
                created_at=kw.created_at,
                updated_at=kw.updated_at,
            )
            for kw in keywords
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
