"""Article service for business logic."""

import logging
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article, ArticleImage
from app.schemas.article import ArticleCreate, ArticleUpdate

logger = logging.getLogger(__name__)


class ArticleService:
    """Service for article operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ArticleCreate) -> Article:
        """Create a new article."""
        article = Article(
            workspace_id=data.workspace_id,
            plan_id=data.plan_id,
            title=data.title,
            content=data.content,
            status=data.status,
            ai_model_used=data.ai_model_used,
            word_count=data.word_count,
            generation_metadata=data.metadata or {},
        )
        self.db.add(article)
        await self.db.commit()
        await self.db.refresh(article)
        logger.info(f"Created article: {article.id}")
        return article

    async def create_from_generation(
        self,
        workspace_id: UUID,
        plan_id: Optional[UUID],
        title: str,
        content: str,
        model: str,
        cost_usd: Decimal,
        word_count: int,
        metadata: Optional[dict] = None,
    ) -> Article:
        """Create an article from generation results."""
        article = Article(
            workspace_id=workspace_id,
            plan_id=plan_id,
            title=title,
            content=content,
            status="draft",
            ai_model_used=model,
            cost_usd=cost_usd,
            word_count=word_count,
            generation_metadata=metadata or {},
        )
        self.db.add(article)
        await self.db.commit()
        await self.db.refresh(article)
        logger.info(f"Created generated article: {article.id}")
        return article

    async def get_by_id(self, article_id: UUID) -> Optional[Article]:
        """Get an article by ID with images."""
        result = await self.db.execute(
            select(Article)
            .options(selectinload(Article.images))
            .where(Article.id == article_id)
        )
        return result.scalar_one_or_none()

    async def get_by_workspace(
        self,
        workspace_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Article], int]:
        """Get articles for a workspace with pagination."""
        query = select(Article).where(Article.workspace_id == workspace_id)

        if status:
            query = query.where(Article.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and order
        query = query.order_by(Article.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        query = query.options(selectinload(Article.images))

        result = await self.db.execute(query)
        articles = result.scalars().all()

        return list(articles), total

    async def update(
        self, article_id: UUID, data: ArticleUpdate
    ) -> Optional[Article]:
        """Update an article."""
        article = await self.get_by_id(article_id)
        if not article:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(article, field, value)

        await self.db.commit()
        await self.db.refresh(article)
        logger.info(f"Updated article: {article_id}")
        return article

    async def delete(self, article_id: UUID) -> bool:
        """Delete an article."""
        article = await self.get_by_id(article_id)
        if not article:
            return False

        await self.db.delete(article)
        await self.db.commit()
        logger.info(f"Deleted article: {article_id}")
        return True

    async def add_image(
        self,
        article_id: UUID,
        filename: str,
        original_filename: str,
        content_type: str,
        size_bytes: int,
        storage_path: str,
    ) -> Optional[ArticleImage]:
        """Add an image to an article."""
        article = await self.get_by_id(article_id)
        if not article:
            return None

        image = ArticleImage(
            article_id=article_id,
            filename=filename,
            original_filename=original_filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_path=storage_path,
        )
        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)
        logger.info(f"Added image {image.id} to article {article_id}")
        return image

    async def get_images(self, article_id: UUID) -> List[ArticleImage]:
        """Get all images for an article."""
        result = await self.db.execute(
            select(ArticleImage).where(ArticleImage.article_id == article_id)
        )
        return list(result.scalars().all())

    async def delete_image(self, image_id: UUID) -> bool:
        """Delete an image."""
        result = await self.db.execute(
            select(ArticleImage).where(ArticleImage.id == image_id)
        )
        image = result.scalar_one_or_none()
        if not image:
            return False

        await self.db.delete(image)
        await self.db.commit()
        logger.info(f"Deleted image: {image_id}")
        return True
