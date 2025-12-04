"""Tests for service layer."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.topic_cluster import TopicCluster, ClusterKeyword
from app.models.content_plan import ContentPlan
from app.schemas.seo_strategy import (
    TopicClusterCreate,
    TopicClusterUpdate,
    ContentPlanCreate,
    ContentPlanUpdate,
)
from app.services.topic_cluster_service import TopicClusterService
from app.services.content_plan_service import ContentPlanService


class TestTopicClusterService:
    """Tests for TopicClusterService."""

    @pytest.mark.asyncio
    async def test_create_topic_cluster(self, db_session: AsyncSession):
        """Test creating a topic cluster."""
        service = TopicClusterService(db_session)
        workspace_id = uuid4()

        data = TopicClusterCreate(
            workspace_id=workspace_id,
            name="Test Cluster",
            type="pillar",
            description="Test description",
        )
        cluster = await service.create(data)

        assert cluster.id is not None
        assert cluster.name == "Test Cluster"
        assert cluster.type == "pillar"
        assert cluster.workspace_id == workspace_id

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession):
        """Test getting a topic cluster by ID."""
        service = TopicClusterService(db_session)
        workspace_id = uuid4()

        # Create cluster
        data = TopicClusterCreate(
            workspace_id=workspace_id,
            name="Get Test",
            type="cluster",
        )
        created = await service.create(data)

        # Get cluster
        cluster = await service.get_by_id(created.id)
        assert cluster is not None
        assert cluster.id == created.id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """Test getting non-existent cluster returns None."""
        service = TopicClusterService(db_session)
        cluster = await service.get_by_id(uuid4())
        assert cluster is None

    @pytest.mark.asyncio
    async def test_get_by_workspace(self, db_session: AsyncSession):
        """Test getting clusters by workspace."""
        service = TopicClusterService(db_session)
        workspace_id = uuid4()

        # Create clusters
        for i in range(3):
            data = TopicClusterCreate(
                workspace_id=workspace_id,
                name=f"Cluster {i}",
                type="cluster",
            )
            await service.create(data)

        # Get clusters
        clusters, total = await service.get_by_workspace(workspace_id)
        assert total == 3
        assert len(clusters) == 3

    @pytest.mark.asyncio
    async def test_update_topic_cluster(self, db_session: AsyncSession):
        """Test updating a topic cluster."""
        service = TopicClusterService(db_session)
        workspace_id = uuid4()

        # Create cluster
        data = TopicClusterCreate(
            workspace_id=workspace_id,
            name="Original",
            type="cluster",
        )
        created = await service.create(data)

        # Update cluster
        update_data = TopicClusterUpdate(
            name="Updated",
            description="New description",
        )
        updated = await service.update(created.id, update_data)

        assert updated is not None
        assert updated.name == "Updated"
        assert updated.description == "New description"

    @pytest.mark.asyncio
    async def test_delete_topic_cluster(self, db_session: AsyncSession):
        """Test deleting a topic cluster."""
        service = TopicClusterService(db_session)
        workspace_id = uuid4()

        # Create cluster
        data = TopicClusterCreate(
            workspace_id=workspace_id,
            name="To Delete",
            type="cluster",
        )
        created = await service.create(data)

        # Delete cluster
        result = await service.delete(created.id)
        assert result is True

        # Verify deleted
        cluster = await service.get_by_id(created.id)
        assert cluster is None

    @pytest.mark.asyncio
    async def test_add_keyword(self, db_session: AsyncSession):
        """Test adding a keyword to a cluster."""
        service = TopicClusterService(db_session)
        workspace_id = uuid4()

        # Create cluster
        data = TopicClusterCreate(
            workspace_id=workspace_id,
            name="Keyword Cluster",
            type="cluster",
        )
        cluster = await service.create(data)

        # Add keyword
        keyword_id = uuid4()
        cluster_keyword = await service.add_keyword(cluster.id, keyword_id, True)

        assert cluster_keyword is not None
        assert cluster_keyword.keyword_id == keyword_id
        assert cluster_keyword.is_primary is True

    @pytest.mark.asyncio
    async def test_add_duplicate_keyword(self, db_session: AsyncSession):
        """Test adding duplicate keyword returns None."""
        service = TopicClusterService(db_session)
        workspace_id = uuid4()

        # Create cluster
        data = TopicClusterCreate(
            workspace_id=workspace_id,
            name="Dupe Cluster",
            type="cluster",
        )
        cluster = await service.create(data)

        # Add keyword twice
        keyword_id = uuid4()
        await service.add_keyword(cluster.id, keyword_id)
        result = await service.add_keyword(cluster.id, keyword_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_remove_keyword(self, db_session: AsyncSession):
        """Test removing a keyword from a cluster."""
        service = TopicClusterService(db_session)
        workspace_id = uuid4()

        # Create cluster and add keyword
        data = TopicClusterCreate(
            workspace_id=workspace_id,
            name="Remove Cluster",
            type="cluster",
        )
        cluster = await service.create(data)
        keyword_id = uuid4()
        await service.add_keyword(cluster.id, keyword_id)

        # Remove keyword
        result = await service.remove_keyword(cluster.id, keyword_id)
        assert result is True

        # Verify removed
        keywords = await service.get_cluster_keywords(cluster.id)
        assert len(keywords) == 0

    @pytest.mark.asyncio
    async def test_get_keyword_count(self, db_session: AsyncSession):
        """Test getting keyword count for a cluster."""
        service = TopicClusterService(db_session)
        workspace_id = uuid4()

        # Create cluster and add keywords
        data = TopicClusterCreate(
            workspace_id=workspace_id,
            name="Count Cluster",
            type="cluster",
        )
        cluster = await service.create(data)

        for _ in range(5):
            await service.add_keyword(cluster.id, uuid4())

        count = await service.get_keyword_count(cluster.id)
        assert count == 5


class TestContentPlanService:
    """Tests for ContentPlanService."""

    @pytest.mark.asyncio
    async def test_create_content_plan(self, db_session: AsyncSession):
        """Test creating a content plan."""
        service = ContentPlanService(db_session)
        workspace_id = uuid4()
        user_id = uuid4()

        data = ContentPlanCreate(
            workspace_id=workspace_id,
            title="Test Plan",
            priority="high",
            target_keywords=["keyword1", "keyword2"],
            status="draft",
        )
        plan = await service.create(data, user_id=user_id)

        assert plan.id is not None
        assert plan.title == "Test Plan"
        assert plan.priority == "high"
        assert plan.created_by == user_id

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession):
        """Test getting a content plan by ID."""
        service = ContentPlanService(db_session)
        workspace_id = uuid4()

        # Create plan
        data = ContentPlanCreate(
            workspace_id=workspace_id,
            title="Get Test",
        )
        created = await service.create(data)

        # Get plan
        plan = await service.get_by_id(created.id)
        assert plan is not None
        assert plan.id == created.id

    @pytest.mark.asyncio
    async def test_get_by_workspace(self, db_session: AsyncSession):
        """Test getting plans by workspace."""
        service = ContentPlanService(db_session)
        workspace_id = uuid4()

        # Create plans
        for i in range(3):
            data = ContentPlanCreate(
                workspace_id=workspace_id,
                title=f"Plan {i}",
            )
            await service.create(data)

        # Get plans
        plans, total = await service.get_by_workspace(workspace_id)
        assert total == 3
        assert len(plans) == 3

    @pytest.mark.asyncio
    async def test_get_by_workspace_with_filters(self, db_session: AsyncSession):
        """Test getting plans with filters."""
        service = ContentPlanService(db_session)
        workspace_id = uuid4()

        # Create plans with different statuses
        await service.create(ContentPlanCreate(
            workspace_id=workspace_id,
            title="Draft",
            status="draft",
        ))
        await service.create(ContentPlanCreate(
            workspace_id=workspace_id,
            title="Approved",
            status="approved",
        ))

        # Filter by status
        plans, total = await service.get_by_workspace(workspace_id, status="draft")
        assert total == 1
        assert plans[0].status == "draft"

    @pytest.mark.asyncio
    async def test_update_content_plan(self, db_session: AsyncSession):
        """Test updating a content plan."""
        service = ContentPlanService(db_session)
        workspace_id = uuid4()

        # Create plan
        data = ContentPlanCreate(
            workspace_id=workspace_id,
            title="Original",
            priority="low",
        )
        created = await service.create(data)

        # Update plan
        update_data = ContentPlanUpdate(
            title="Updated",
            priority="high",
            status="approved",
        )
        updated = await service.update(created.id, update_data)

        assert updated is not None
        assert updated.title == "Updated"
        assert updated.priority == "high"
        assert updated.status == "approved"

    @pytest.mark.asyncio
    async def test_delete_content_plan(self, db_session: AsyncSession):
        """Test deleting a content plan."""
        service = ContentPlanService(db_session)
        workspace_id = uuid4()

        # Create plan
        data = ContentPlanCreate(
            workspace_id=workspace_id,
            title="To Delete",
        )
        created = await service.create(data)

        # Delete plan
        result = await service.delete(created.id)
        assert result is True

        # Verify deleted
        plan = await service.get_by_id(created.id)
        assert plan is None
