"""SEO Score service for business logic."""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.seo_score import SeoScore, DEFAULT_CHECKLIST
from app.schemas.seo_score import SeoScoreCreate, SeoScoreUpdate

logger = logging.getLogger(__name__)


class SeoScoreService:
    """Service for SEO score operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: SeoScoreCreate) -> SeoScore:
        """Create a new SEO score entry."""
        checklist = data.checklist if data.checklist else DEFAULT_CHECKLIST.copy()
        
        seo_score = SeoScore(
            article_id=data.article_id,
            workspace_id=data.workspace_id,
            checklist=checklist,
            status=data.status,
        )
        
        # Calculate manual score based on checklist
        seo_score.manual_score = seo_score.calculate_score()
        
        self.db.add(seo_score)
        await self.db.commit()
        await self.db.refresh(seo_score)
        logger.info(f"Created SEO score: {seo_score.id}")
        return seo_score

    async def get_by_id(self, score_id: UUID) -> Optional[SeoScore]:
        """Get an SEO score by ID."""
        result = await self.db.execute(
            select(SeoScore).where(SeoScore.id == score_id)
        )
        return result.scalar_one_or_none()

    async def get_by_article_id(self, article_id: UUID) -> Optional[SeoScore]:
        """Get an SEO score by article ID."""
        result = await self.db.execute(
            select(SeoScore)
            .where(SeoScore.article_id == article_id)
            .order_by(SeoScore.created_at.desc())
        )
        return result.scalar_one_or_none()

    async def get_by_workspace(
        self,
        workspace_id: UUID,
        article_id: Optional[UUID] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[SeoScore], int]:
        """Get SEO scores for a workspace with pagination."""
        query = select(SeoScore).where(SeoScore.workspace_id == workspace_id)

        if article_id:
            query = query.where(SeoScore.article_id == article_id)
        if status:
            query = query.where(SeoScore.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.order_by(SeoScore.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        scores = result.scalars().all()

        return list(scores), total

    async def update(
        self, score_id: UUID, data: SeoScoreUpdate
    ) -> Optional[SeoScore]:
        """Update an SEO score."""
        seo_score = await self.get_by_id(score_id)
        if not seo_score:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(seo_score, field, value)

        # Recalculate manual score if checklist was updated
        if "checklist" in update_data:
            seo_score.manual_score = seo_score.calculate_score()

        await self.db.commit()
        await self.db.refresh(seo_score)
        logger.info(f"Updated SEO score: {score_id}")
        return seo_score

    async def delete(self, score_id: UUID) -> bool:
        """Delete an SEO score."""
        seo_score = await self.get_by_id(score_id)
        if not seo_score:
            return False

        await self.db.delete(seo_score)
        await self.db.commit()
        logger.info(f"Deleted SEO score: {score_id}")
        return True

    @staticmethod
    def calculate_score_from_checklist(checklist: dict) -> dict:
        """Calculate score from a checklist.
        
        Returns a dictionary with score details.
        """
        if not checklist:
            return {
                "score": 0,
                "total_items": 0,
                "checked_items": 0,
                "checklist": {},
            }

        total_items = len(checklist)
        checked_items = sum(1 for value in checklist.values() if value is True)
        score = int((checked_items / total_items) * 100) if total_items > 0 else 0

        return {
            "score": score,
            "total_items": total_items,
            "checked_items": checked_items,
            "checklist": checklist,
        }
