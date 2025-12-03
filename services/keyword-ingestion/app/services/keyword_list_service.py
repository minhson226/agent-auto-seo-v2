"""Keyword list service for business logic."""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.keyword import Keyword
from app.models.keyword_list import KeywordList
from app.schemas.keyword import (
    IntentCount,
    KeywordListCreate,
    KeywordListStats,
    StatusCount,
)

logger = logging.getLogger(__name__)


class KeywordListService:
    """Service for keyword list operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        data: KeywordListCreate,
        user_id: UUID,
        source: str,
        source_file_url: Optional[str] = None,
    ) -> KeywordList:
        """Create a new keyword list.

        Args:
            data: Keyword list creation data
            user_id: ID of the user creating the list
            source: Source of the keywords (csv_upload, txt_upload, etc.)
            source_file_url: URL of the source file in S3

        Returns:
            Created KeywordList
        """
        keyword_list = KeywordList(
            workspace_id=data.workspace_id,
            name=data.name,
            description=data.description,
            source=source,
            source_file_url=source_file_url,
            status="processing",
            created_by=user_id,
        )
        self.db.add(keyword_list)
        await self.db.commit()
        await self.db.refresh(keyword_list)
        return keyword_list

    async def get_by_id(self, list_id: UUID) -> Optional[KeywordList]:
        """Get a keyword list by ID.

        Args:
            list_id: ID of the keyword list

        Returns:
            KeywordList if found, None otherwise
        """
        result = await self.db.execute(
            select(KeywordList).where(KeywordList.id == list_id)
        )
        return result.scalar_one_or_none()

    async def get_by_workspace(
        self,
        workspace_id: UUID,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[KeywordList], int]:
        """Get keyword lists by workspace.

        Args:
            workspace_id: ID of the workspace
            status: Optional status filter
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (list of KeywordLists, total count)
        """
        query = select(KeywordList).where(KeywordList.workspace_id == workspace_id)

        if status:
            query = query.where(KeywordList.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(KeywordList.created_at.desc())
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        keyword_lists = result.scalars().all()

        return list(keyword_lists), total

    async def delete(self, list_id: UUID) -> bool:
        """Delete a keyword list.

        Args:
            list_id: ID of the keyword list

        Returns:
            True if deleted, False if not found
        """
        keyword_list = await self.get_by_id(list_id)
        if not keyword_list:
            return False

        await self.db.delete(keyword_list)
        await self.db.commit()
        return True

    async def add_keywords(
        self,
        list_id: UUID,
        keywords: List[Tuple[str, str]],
    ) -> int:
        """Add keywords to a list.

        Args:
            list_id: ID of the keyword list
            keywords: List of tuples (original_text, normalized_text)

        Returns:
            Number of keywords added
        """
        added = 0
        for text, normalized_text in keywords:
            keyword = Keyword(
                list_id=list_id,
                text=text,
                normalized_text=normalized_text,
                status="pending",
                intent="unknown",
            )
            self.db.add(keyword)
            added += 1

        await self.db.commit()
        return added

    async def update_status(
        self,
        list_id: UUID,
        status: str,
        error_message: Optional[str] = None,
        total_keywords: Optional[int] = None,
    ):
        """Update the status of a keyword list.

        Args:
            list_id: ID of the keyword list
            status: New status
            error_message: Optional error message
            total_keywords: Optional total keyword count
        """
        keyword_list = await self.get_by_id(list_id)
        if keyword_list:
            keyword_list.status = status
            if error_message is not None:
                keyword_list.error_message = error_message
            if total_keywords is not None:
                keyword_list.total_keywords = total_keywords
            if status == "completed":
                keyword_list.processed_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def get_keywords(
        self,
        list_id: UUID,
        status: Optional[str] = None,
        intent: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Keyword], int]:
        """Get keywords from a list.

        Args:
            list_id: ID of the keyword list
            status: Optional status filter
            intent: Optional intent filter
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (list of Keywords, total count)
        """
        query = select(Keyword).where(Keyword.list_id == list_id)

        if status:
            query = query.where(Keyword.status == status)
        if intent:
            query = query.where(Keyword.intent == intent)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Keyword.created_at.desc())
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        keywords = result.scalars().all()

        return list(keywords), total

    async def get_stats(self, list_id: UUID) -> KeywordListStats:
        """Get statistics for a keyword list.

        Args:
            list_id: ID of the keyword list

        Returns:
            KeywordListStats with counts
        """
        # Get total count
        total_query = select(func.count()).where(Keyword.list_id == list_id)
        total_result = await self.db.execute(total_query)
        total = total_result.scalar() or 0

        # Get status counts
        status_query = (
            select(Keyword.status, func.count())
            .where(Keyword.list_id == list_id)
            .group_by(Keyword.status)
        )
        status_result = await self.db.execute(status_query)
        status_counts = dict(status_result.fetchall())

        # Get intent counts
        intent_query = (
            select(Keyword.intent, func.count())
            .where(Keyword.list_id == list_id)
            .group_by(Keyword.intent)
        )
        intent_result = await self.db.execute(intent_query)
        intent_counts = dict(intent_result.fetchall())

        return KeywordListStats(
            total=total,
            by_status=StatusCount(
                pending=status_counts.get("pending", 0),
                processed=status_counts.get("processed", 0),
                assigned=status_counts.get("assigned", 0),
            ),
            by_intent=IntentCount(
                unknown=intent_counts.get("unknown", 0),
                informational=intent_counts.get("informational", 0),
                commercial=intent_counts.get("commercial", 0),
                navigational=intent_counts.get("navigational", 0),
                transactional=intent_counts.get("transactional", 0),
            ),
        )
