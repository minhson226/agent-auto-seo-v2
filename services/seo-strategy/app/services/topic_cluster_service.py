"""Topic Cluster service for business logic."""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.topic_cluster import ClusterKeyword, TopicCluster
from app.schemas.seo_strategy import TopicClusterCreate, TopicClusterUpdate

logger = logging.getLogger(__name__)


class TopicClusterService:
    """Service for topic cluster operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: TopicClusterCreate) -> TopicCluster:
        """Create a new topic cluster."""
        cluster = TopicCluster(
            workspace_id=data.workspace_id,
            name=data.name,
            type=data.type,
            description=data.description,
            pillar_cluster_id=data.pillar_cluster_id,
            metadata_=data.metadata or {},
        )
        self.db.add(cluster)
        await self.db.commit()
        await self.db.refresh(cluster)
        logger.info(f"Created topic cluster: {cluster.id}")
        return cluster

    async def get_by_id(self, cluster_id: UUID) -> Optional[TopicCluster]:
        """Get a topic cluster by ID."""
        result = await self.db.execute(
            select(TopicCluster).where(TopicCluster.id == cluster_id)
        )
        return result.scalar_one_or_none()

    async def get_by_workspace(
        self,
        workspace_id: UUID,
        cluster_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[TopicCluster], int]:
        """Get topic clusters for a workspace with pagination."""
        query = select(TopicCluster).where(
            TopicCluster.workspace_id == workspace_id
        )

        if cluster_type:
            query = query.where(TopicCluster.type == cluster_type)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        query = query.order_by(TopicCluster.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        clusters = result.scalars().all()

        return list(clusters), total

    async def update(
        self, cluster_id: UUID, data: TopicClusterUpdate
    ) -> Optional[TopicCluster]:
        """Update a topic cluster."""
        cluster = await self.get_by_id(cluster_id)
        if not cluster:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "metadata":
                setattr(cluster, "metadata_", value)
            else:
                setattr(cluster, field, value)

        await self.db.commit()
        await self.db.refresh(cluster)
        logger.info(f"Updated topic cluster: {cluster_id}")
        return cluster

    async def delete(self, cluster_id: UUID) -> bool:
        """Delete a topic cluster."""
        cluster = await self.get_by_id(cluster_id)
        if not cluster:
            return False

        await self.db.delete(cluster)
        await self.db.commit()
        logger.info(f"Deleted topic cluster: {cluster_id}")
        return True

    async def add_keyword(
        self, cluster_id: UUID, keyword_id: UUID, is_primary: bool = False
    ) -> Optional[ClusterKeyword]:
        """Add a keyword to a cluster."""
        # Check if cluster exists
        cluster = await self.get_by_id(cluster_id)
        if not cluster:
            return None

        # Check if keyword is already in cluster
        existing = await self.db.execute(
            select(ClusterKeyword).where(
                ClusterKeyword.cluster_id == cluster_id,
                ClusterKeyword.keyword_id == keyword_id,
            )
        )
        if existing.scalar_one_or_none():
            logger.warning(f"Keyword {keyword_id} already in cluster {cluster_id}")
            return None

        cluster_keyword = ClusterKeyword(
            cluster_id=cluster_id,
            keyword_id=keyword_id,
            is_primary=is_primary,
        )
        self.db.add(cluster_keyword)
        await self.db.commit()
        await self.db.refresh(cluster_keyword)
        logger.info(f"Added keyword {keyword_id} to cluster {cluster_id}")
        return cluster_keyword

    async def add_keywords_batch(
        self, cluster_id: UUID, keyword_ids: List[UUID], is_primary: bool = False
    ) -> List[ClusterKeyword]:
        """Add multiple keywords to a cluster."""
        cluster = await self.get_by_id(cluster_id)
        if not cluster:
            return []

        # Get existing keyword IDs in this cluster
        existing_result = await self.db.execute(
            select(ClusterKeyword.keyword_id).where(
                ClusterKeyword.cluster_id == cluster_id
            )
        )
        existing_ids = {row[0] for row in existing_result.all()}

        # Add only keywords that are not already in the cluster
        added = []
        for keyword_id in keyword_ids:
            if keyword_id not in existing_ids:
                cluster_keyword = ClusterKeyword(
                    cluster_id=cluster_id,
                    keyword_id=keyword_id,
                    is_primary=is_primary,
                )
                self.db.add(cluster_keyword)
                added.append(cluster_keyword)

        if added:
            await self.db.commit()
            for ck in added:
                await self.db.refresh(ck)
            logger.info(f"Added {len(added)} keywords to cluster {cluster_id}")

        return added

    async def remove_keyword(self, cluster_id: UUID, keyword_id: UUID) -> bool:
        """Remove a keyword from a cluster."""
        result = await self.db.execute(
            delete(ClusterKeyword).where(
                ClusterKeyword.cluster_id == cluster_id,
                ClusterKeyword.keyword_id == keyword_id,
            )
        )
        await self.db.commit()
        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Removed keyword {keyword_id} from cluster {cluster_id}")
        return deleted

    async def get_cluster_keywords(
        self, cluster_id: UUID
    ) -> List[ClusterKeyword]:
        """Get all keywords in a cluster."""
        result = await self.db.execute(
            select(ClusterKeyword).where(ClusterKeyword.cluster_id == cluster_id)
        )
        return list(result.scalars().all())

    async def get_keyword_count(self, cluster_id: UUID) -> int:
        """Get the count of keywords in a cluster."""
        result = await self.db.execute(
            select(func.count()).select_from(ClusterKeyword).where(
                ClusterKeyword.cluster_id == cluster_id
            )
        )
        return result.scalar() or 0
