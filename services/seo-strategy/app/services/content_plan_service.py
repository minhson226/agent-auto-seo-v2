"""Content Plan service for business logic."""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_plan import ContentPlan
from app.schemas.seo_strategy import ContentPlanCreate, ContentPlanUpdate

logger = logging.getLogger(__name__)


class ContentPlanService:
    """Service for content plan operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self, data: ContentPlanCreate, user_id: Optional[UUID] = None
    ) -> ContentPlan:
        """Create a new content plan."""
        content_plan = ContentPlan(
            workspace_id=data.workspace_id,
            cluster_id=data.cluster_id,
            title=data.title,
            priority=data.priority,
            target_keywords_json=data.target_keywords or [],
            competitors_data=data.competitors_data or {},
            status=data.status,
            estimated_word_count=data.estimated_word_count,
            notes=data.notes,
            created_by=user_id,
        )
        self.db.add(content_plan)
        await self.db.commit()
        await self.db.refresh(content_plan)
        logger.info(f"Created content plan: {content_plan.id}")
        return content_plan

    async def get_by_id(self, plan_id: UUID) -> Optional[ContentPlan]:
        """Get a content plan by ID."""
        result = await self.db.execute(
            select(ContentPlan).where(ContentPlan.id == plan_id)
        )
        return result.scalar_one_or_none()

    async def get_by_workspace(
        self,
        workspace_id: UUID,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        cluster_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ContentPlan], int]:
        """Get content plans for a workspace with pagination."""
        query = select(ContentPlan).where(
            ContentPlan.workspace_id == workspace_id
        )

        if status:
            query = query.where(ContentPlan.status == status)
        if priority:
            query = query.where(ContentPlan.priority == priority)
        if cluster_id:
            query = query.where(ContentPlan.cluster_id == cluster_id)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.order_by(ContentPlan.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        plans = result.scalars().all()

        return list(plans), total

    async def update(
        self, plan_id: UUID, data: ContentPlanUpdate
    ) -> Optional[ContentPlan]:
        """Update a content plan."""
        content_plan = await self.get_by_id(plan_id)
        if not content_plan:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "target_keywords":
                setattr(content_plan, "target_keywords_json", value)
            else:
                setattr(content_plan, field, value)

        await self.db.commit()
        await self.db.refresh(content_plan)
        logger.info(f"Updated content plan: {plan_id}")
        return content_plan

    async def delete(self, plan_id: UUID) -> bool:
        """Delete a content plan."""
        content_plan = await self.get_by_id(plan_id)
        if not content_plan:
            return False

        await self.db.delete(content_plan)
        await self.db.commit()
        logger.info(f"Deleted content plan: {plan_id}")
        return True
