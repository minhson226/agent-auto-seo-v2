"""Tests for SEO Score service."""

import pytest
import pytest_asyncio
from uuid import uuid4

from app.core.constants import DEFAULT_CHECKLIST
from app.models.seo_score import SeoScore
from app.schemas.seo_score import SeoScoreCreate, SeoScoreUpdate
from app.services.seo_score_service import SeoScoreService


class TestSeoScoreService:
    """Tests for SeoScoreService."""

    @pytest_asyncio.fixture
    async def service(self, db_session):
        """Create service instance with db session."""
        return SeoScoreService(db_session)

    @pytest.mark.asyncio
    async def test_create_seo_score(self, service, test_workspace_id):
        """Test creating a new SEO score."""
        data = SeoScoreCreate(
            workspace_id=test_workspace_id,
            checklist=DEFAULT_CHECKLIST.copy(),
            status="pending",
        )

        score = await service.create(data)

        assert score is not None
        assert score.workspace_id == test_workspace_id
        assert score.manual_score == 0  # All items are False
        assert score.status == "pending"
        assert score.checklist == DEFAULT_CHECKLIST

    @pytest.mark.asyncio
    async def test_create_seo_score_with_checked_items(self, service, test_workspace_id):
        """Test creating SEO score with some checked items."""
        checklist = DEFAULT_CHECKLIST.copy()
        checklist["title_contains_keyword"] = True
        checklist["h1_present"] = True
        checklist["meta_description"] = True

        data = SeoScoreCreate(
            workspace_id=test_workspace_id,
            checklist=checklist,
            status="pending",
        )

        score = await service.create(data)

        assert score is not None
        assert score.manual_score == 30  # 3/10 * 100 = 30

    @pytest.mark.asyncio
    async def test_get_by_id(self, service, test_workspace_id):
        """Test getting SEO score by ID."""
        data = SeoScoreCreate(
            workspace_id=test_workspace_id,
            status="pending",
        )
        created = await service.create(data)

        score = await service.get_by_id(created.id)

        assert score is not None
        assert score.id == created.id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, service):
        """Test getting non-existent SEO score."""
        score = await service.get_by_id(uuid4())
        assert score is None

    @pytest.mark.asyncio
    async def test_get_by_workspace(self, service, test_workspace_id):
        """Test getting SEO scores by workspace."""
        # Create multiple scores
        for _ in range(3):
            data = SeoScoreCreate(
                workspace_id=test_workspace_id,
                status="pending",
            )
            await service.create(data)

        scores, total = await service.get_by_workspace(
            workspace_id=test_workspace_id,
            page=1,
            page_size=10,
        )

        assert total == 3
        assert len(scores) == 3

    @pytest.mark.asyncio
    async def test_get_by_workspace_with_filter(self, service, test_workspace_id):
        """Test filtering SEO scores by status."""
        # Create scores with different statuses
        for status in ["pending", "completed", "reviewed"]:
            data = SeoScoreCreate(
                workspace_id=test_workspace_id,
                status=status,
            )
            await service.create(data)

        scores, total = await service.get_by_workspace(
            workspace_id=test_workspace_id,
            status="completed",
            page=1,
            page_size=10,
        )

        assert total == 1
        assert scores[0].status == "completed"

    @pytest.mark.asyncio
    async def test_update_seo_score(self, service, test_workspace_id):
        """Test updating an SEO score."""
        data = SeoScoreCreate(
            workspace_id=test_workspace_id,
            status="pending",
        )
        created = await service.create(data)

        update_data = SeoScoreUpdate(status="completed")
        updated = await service.update(created.id, update_data)

        assert updated is not None
        assert updated.status == "completed"

    @pytest.mark.asyncio
    async def test_update_checklist_recalculates_score(self, service, test_workspace_id):
        """Test that updating checklist recalculates the score."""
        data = SeoScoreCreate(
            workspace_id=test_workspace_id,
            status="pending",
        )
        created = await service.create(data)
        assert created.manual_score == 0

        # Update checklist with 5 checked items
        new_checklist = DEFAULT_CHECKLIST.copy()
        new_checklist["title_contains_keyword"] = True
        new_checklist["h1_present"] = True
        new_checklist["h2_count_adequate"] = True
        new_checklist["keyword_density_ok"] = True
        new_checklist["images_have_alt"] = True

        update_data = SeoScoreUpdate(checklist=new_checklist)
        updated = await service.update(created.id, update_data)

        assert updated.manual_score == 50  # 5/10 * 100 = 50

    @pytest.mark.asyncio
    async def test_delete_seo_score(self, service, test_workspace_id):
        """Test deleting an SEO score."""
        data = SeoScoreCreate(
            workspace_id=test_workspace_id,
            status="pending",
        )
        created = await service.create(data)

        deleted = await service.delete(created.id)
        assert deleted is True

        score = await service.get_by_id(created.id)
        assert score is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self, service):
        """Test deleting non-existent SEO score."""
        deleted = await service.delete(uuid4())
        assert deleted is False

    def test_calculate_score_from_checklist(self):
        """Test static score calculation method."""
        checklist = {
            "item1": True,
            "item2": True,
            "item3": False,
            "item4": True,
            "item5": False,
        }

        result = SeoScoreService.calculate_score_from_checklist(checklist)

        assert result["score"] == 60  # 3/5 * 100 = 60
        assert result["total_items"] == 5
        assert result["checked_items"] == 3

    def test_calculate_score_from_empty_checklist(self):
        """Test score calculation with empty checklist."""
        result = SeoScoreService.calculate_score_from_checklist({})

        assert result["score"] == 0
        assert result["total_items"] == 0
        assert result["checked_items"] == 0

    def test_calculate_score_all_checked(self):
        """Test score calculation with all items checked."""
        checklist = {
            "item1": True,
            "item2": True,
            "item3": True,
        }

        result = SeoScoreService.calculate_score_from_checklist(checklist)

        assert result["score"] == 100
        assert result["checked_items"] == 3
