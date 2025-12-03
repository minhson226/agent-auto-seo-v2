"""Integration tests for keyword list service."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.keyword import Keyword
from app.models.keyword_list import KeywordList
from app.schemas.keyword import KeywordListCreate
from app.services.keyword_list_service import KeywordListService


class TestKeywordListService:
    """Integration tests for KeywordListService."""

    @pytest.mark.asyncio
    async def test_create_keyword_list(self, db_session: AsyncSession):
        """Test creating a keyword list."""
        service = KeywordListService(db_session)
        workspace_id = uuid4()
        user_id = uuid4()

        data = KeywordListCreate(
            name="Test List",
            description="Test description",
            workspace_id=workspace_id,
        )

        result = await service.create(
            data=data,
            user_id=user_id,
            source="csv_upload",
            source_file_url="s3://bucket/file.csv",
        )

        assert result.id is not None
        assert result.name == "Test List"
        assert result.description == "Test description"
        assert result.workspace_id == workspace_id
        assert result.created_by == user_id
        assert result.source == "csv_upload"
        assert result.status == "processing"

    @pytest.mark.asyncio
    async def test_get_by_id(self, db_session: AsyncSession):
        """Test getting a keyword list by ID."""
        service = KeywordListService(db_session)
        workspace_id = uuid4()
        user_id = uuid4()

        # Create a list
        data = KeywordListCreate(
            name="Test List",
            workspace_id=workspace_id,
        )
        created = await service.create(data, user_id, "csv_upload")

        # Get by ID
        result = await service.get_by_id(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.name == "Test List"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, db_session: AsyncSession):
        """Test getting non-existent keyword list returns None."""
        service = KeywordListService(db_session)
        result = await service.get_by_id(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_workspace(self, db_session: AsyncSession):
        """Test getting keyword lists by workspace."""
        service = KeywordListService(db_session)
        workspace_id = uuid4()
        user_id = uuid4()

        # Create multiple lists
        for i in range(3):
            data = KeywordListCreate(
                name=f"Test List {i}",
                workspace_id=workspace_id,
            )
            await service.create(data, user_id, "csv_upload")

        # Get by workspace
        lists, total = await service.get_by_workspace(workspace_id)

        assert total == 3
        assert len(lists) == 3

    @pytest.mark.asyncio
    async def test_get_by_workspace_with_status_filter(self, db_session: AsyncSession):
        """Test getting keyword lists filtered by status."""
        service = KeywordListService(db_session)
        workspace_id = uuid4()
        user_id = uuid4()

        # Create lists
        data1 = KeywordListCreate(name="List 1", workspace_id=workspace_id)
        list1 = await service.create(data1, user_id, "csv_upload")

        data2 = KeywordListCreate(name="List 2", workspace_id=workspace_id)
        await service.create(data2, user_id, "csv_upload")

        # Update one to completed
        await service.update_status(list1.id, "completed", total_keywords=10)

        # Filter by status
        lists, total = await service.get_by_workspace(workspace_id, status="completed")

        assert total == 1
        assert len(lists) == 1
        assert lists[0].status == "completed"

    @pytest.mark.asyncio
    async def test_get_by_workspace_pagination(self, db_session: AsyncSession):
        """Test pagination when getting keyword lists."""
        service = KeywordListService(db_session)
        workspace_id = uuid4()
        user_id = uuid4()

        # Create 5 lists
        for i in range(5):
            data = KeywordListCreate(
                name=f"Test List {i}",
                workspace_id=workspace_id,
            )
            await service.create(data, user_id, "csv_upload")

        # Get first page
        lists, total = await service.get_by_workspace(
            workspace_id, page=1, page_size=2
        )

        assert total == 5
        assert len(lists) == 2

        # Get second page
        lists, total = await service.get_by_workspace(
            workspace_id, page=2, page_size=2
        )

        assert total == 5
        assert len(lists) == 2

    @pytest.mark.asyncio
    async def test_delete_keyword_list(self, db_session: AsyncSession):
        """Test deleting a keyword list."""
        service = KeywordListService(db_session)
        workspace_id = uuid4()
        user_id = uuid4()

        # Create a list
        data = KeywordListCreate(name="Test List", workspace_id=workspace_id)
        created = await service.create(data, user_id, "csv_upload")

        # Delete
        result = await service.delete(created.id)
        assert result is True

        # Verify deleted
        found = await service.get_by_id(created.id)
        assert found is None

    @pytest.mark.asyncio
    async def test_delete_not_found(self, db_session: AsyncSession):
        """Test deleting non-existent list returns False."""
        service = KeywordListService(db_session)
        result = await service.delete(uuid4())
        assert result is False

    @pytest.mark.asyncio
    async def test_add_keywords(self, db_session: AsyncSession):
        """Test adding keywords to a list."""
        service = KeywordListService(db_session)
        workspace_id = uuid4()
        user_id = uuid4()

        # Create a list
        data = KeywordListCreate(name="Test List", workspace_id=workspace_id)
        kw_list = await service.create(data, user_id, "csv_upload")

        # Add keywords
        keywords = [
            ("Apple", "apple"),
            ("Banana", "banana"),
            ("Cherry", "cherry"),
        ]
        count = await service.add_keywords(kw_list.id, keywords)

        assert count == 3

    @pytest.mark.asyncio
    async def test_update_status(self, db_session: AsyncSession):
        """Test updating keyword list status."""
        service = KeywordListService(db_session)
        workspace_id = uuid4()
        user_id = uuid4()

        # Create a list
        data = KeywordListCreate(name="Test List", workspace_id=workspace_id)
        kw_list = await service.create(data, user_id, "csv_upload")

        # Update status
        await service.update_status(
            kw_list.id,
            status="completed",
            total_keywords=10,
        )

        # Verify
        updated = await service.get_by_id(kw_list.id)
        assert updated.status == "completed"
        assert updated.total_keywords == 10
        assert updated.processed_at is not None

    @pytest.mark.asyncio
    async def test_update_status_failed(self, db_session: AsyncSession):
        """Test updating keyword list status to failed with error message."""
        service = KeywordListService(db_session)
        workspace_id = uuid4()
        user_id = uuid4()

        # Create a list
        data = KeywordListCreate(name="Test List", workspace_id=workspace_id)
        kw_list = await service.create(data, user_id, "csv_upload")

        # Update status to failed
        await service.update_status(
            kw_list.id,
            status="failed",
            error_message="Invalid file format",
        )

        # Verify
        updated = await service.get_by_id(kw_list.id)
        assert updated.status == "failed"
        assert updated.error_message == "Invalid file format"

    @pytest.mark.asyncio
    async def test_get_keywords(self, db_session: AsyncSession):
        """Test getting keywords from a list."""
        service = KeywordListService(db_session)
        workspace_id = uuid4()
        user_id = uuid4()

        # Create a list
        data = KeywordListCreate(name="Test List", workspace_id=workspace_id)
        kw_list = await service.create(data, user_id, "csv_upload")

        # Add keywords
        keywords = [
            ("Apple", "apple"),
            ("Banana", "banana"),
            ("Cherry", "cherry"),
        ]
        await service.add_keywords(kw_list.id, keywords)

        # Get keywords
        result, total = await service.get_keywords(kw_list.id)

        assert total == 3
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_keywords_with_filters(self, db_session: AsyncSession):
        """Test getting keywords with filters."""
        service = KeywordListService(db_session)
        workspace_id = uuid4()
        user_id = uuid4()

        # Create a list
        data = KeywordListCreate(name="Test List", workspace_id=workspace_id)
        kw_list = await service.create(data, user_id, "csv_upload")

        # Add keywords
        keywords = [
            ("Apple", "apple"),
            ("Banana", "banana"),
        ]
        await service.add_keywords(kw_list.id, keywords)

        # Get keywords filtered by status
        result, total = await service.get_keywords(kw_list.id, status="pending")

        assert total == 2  # All are pending by default

    @pytest.mark.asyncio
    async def test_get_stats(self, db_session: AsyncSession):
        """Test getting keyword list statistics."""
        service = KeywordListService(db_session)
        workspace_id = uuid4()
        user_id = uuid4()

        # Create a list
        data = KeywordListCreate(name="Test List", workspace_id=workspace_id)
        kw_list = await service.create(data, user_id, "csv_upload")

        # Add keywords
        keywords = [
            ("Apple", "apple"),
            ("Banana", "banana"),
            ("Cherry", "cherry"),
        ]
        await service.add_keywords(kw_list.id, keywords)

        # Get stats
        stats = await service.get_stats(kw_list.id)

        assert stats.total == 3
        assert stats.by_status.pending == 3
        assert stats.by_status.processed == 0
        assert stats.by_intent.unknown == 3
