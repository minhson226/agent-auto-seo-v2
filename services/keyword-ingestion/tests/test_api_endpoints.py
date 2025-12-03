"""Tests for API endpoints."""

import io
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.models.keyword import Keyword
from app.models.keyword_list import KeywordList


class TestKeywordListEndpoints:
    """Tests for keyword list API endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_readiness_check(self, async_client: AsyncClient):
        """Test readiness check endpoint."""
        response = await async_client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    @pytest.mark.asyncio
    async def test_create_keyword_list_unauthorized(self, async_client: AsyncClient):
        """Test creating keyword list without auth fails."""
        response = await async_client.post(
            "/api/v1/keyword-lists",
            data={"name": "Test List", "workspace_id": str(uuid4())},
            files={"file": ("test.csv", b"keyword\napple\n", "text/csv")},
        )
        # 401 = Unauthorized (no credentials provided)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_keyword_list_invalid_file_type(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test creating keyword list with invalid file type fails."""
        response = await async_client.post(
            "/api/v1/keyword-lists",
            data={"name": "Test List", "workspace_id": str(test_workspace_id)},
            files={"file": ("test.xlsx", b"data", "application/vnd.ms-excel")},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "Invalid file format" in response.json()["detail"]

    @pytest.mark.asyncio
    @patch("app.api.v1.keyword_lists.StorageService")
    async def test_create_keyword_list_csv(
        self,
        mock_storage_class,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test creating keyword list with CSV file."""
        # Mock storage service
        mock_storage = AsyncMock()
        mock_storage.upload_file = AsyncMock(return_value="s3://test-bucket/file.csv")
        mock_storage_class.return_value = mock_storage

        # Patch the background task to prevent it from running with a different db session
        with patch("app.api.v1.keyword_lists.process_keywords_background"):
            response = await async_client.post(
                "/api/v1/keyword-lists",
                data={
                    "name": "Test Keywords",
                    "workspace_id": str(test_workspace_id),
                    "description": "Test description",
                },
                files={"file": ("keywords.csv", b"keyword\napple\nbanana\n", "text/csv")},
                headers=auth_headers,
            )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Keywords"
        assert data["status"] == "processing"
        assert data["source"] == "csv_upload"

    @pytest.mark.asyncio
    @patch("app.api.v1.keyword_lists.StorageService")
    async def test_create_keyword_list_txt(
        self,
        mock_storage_class,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test creating keyword list with TXT file."""
        # Mock storage service
        mock_storage = AsyncMock()
        mock_storage.upload_file = AsyncMock(return_value="s3://test-bucket/file.txt")
        mock_storage_class.return_value = mock_storage

        # Patch the background task to prevent it from running with a different db session
        with patch("app.api.v1.keyword_lists.process_keywords_background"):
            response = await async_client.post(
                "/api/v1/keyword-lists",
                data={
                    "name": "Test Keywords TXT",
                    "workspace_id": str(test_workspace_id),
                },
                files={"file": ("keywords.txt", b"apple\nbanana\ncherry\n", "text/plain")},
                headers=auth_headers,
            )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Keywords TXT"
        assert data["source"] == "txt_upload"

    @pytest.mark.asyncio
    async def test_list_keyword_lists_unauthorized(self, async_client: AsyncClient):
        """Test listing keyword lists without auth fails."""
        response = await async_client.get(
            f"/api/v1/keyword-lists?workspace_id={uuid4()}"
        )
        # 401 = Unauthorized (no credentials provided)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_keyword_lists_empty(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test listing keyword lists returns empty when none exist."""
        response = await async_client.get(
            f"/api/v1/keyword-lists?workspace_id={test_workspace_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_get_keyword_list_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test getting non-existent keyword list returns 404."""
        response = await async_client.get(
            f"/api/v1/keyword-lists/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_keyword_list_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test deleting non-existent keyword list returns 404."""
        response = await async_client.delete(
            f"/api/v1/keyword-lists/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_keyword_list_stats_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test getting stats for non-existent keyword list returns 404."""
        response = await async_client.get(
            f"/api/v1/keyword-lists/{uuid4()}/stats",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_keywords_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test listing keywords for non-existent list returns 404."""
        response = await async_client.get(
            f"/api/v1/keyword-lists/{uuid4()}/keywords",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch("app.api.v1.keyword_lists.StorageService")
    async def test_create_and_get_keyword_list(
        self,
        mock_storage_class,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test creating and then retrieving a keyword list."""
        # Mock storage service
        mock_storage = AsyncMock()
        mock_storage.upload_file = AsyncMock(return_value="s3://test-bucket/file.csv")
        mock_storage_class.return_value = mock_storage

        # Create list
        with patch("app.api.v1.keyword_lists.process_keywords_background"):
            response = await async_client.post(
                "/api/v1/keyword-lists",
                data={
                    "name": "Test Keyword List",
                    "workspace_id": str(test_workspace_id),
                },
                files={"file": ("keywords.csv", b"keyword\napple\n", "text/csv")},
                headers=auth_headers,
            )

        assert response.status_code == 201
        created = response.json()
        list_id = created["id"]

        # Get the list
        response = await async_client.get(
            f"/api/v1/keyword-lists/{list_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == list_id
        assert data["name"] == "Test Keyword List"

    @pytest.mark.asyncio
    @patch("app.api.v1.keyword_lists.StorageService")
    async def test_create_and_delete_keyword_list(
        self,
        mock_storage_class,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test creating and then deleting a keyword list."""
        # Mock storage service
        mock_storage = AsyncMock()
        mock_storage.upload_file = AsyncMock(return_value="s3://test-bucket/file.csv")
        mock_storage_class.return_value = mock_storage

        # Create list
        with patch("app.api.v1.keyword_lists.process_keywords_background"):
            response = await async_client.post(
                "/api/v1/keyword-lists",
                data={
                    "name": "To Be Deleted",
                    "workspace_id": str(test_workspace_id),
                },
                files={"file": ("keywords.csv", b"keyword\napple\n", "text/csv")},
                headers=auth_headers,
            )

        assert response.status_code == 201
        list_id = response.json()["id"]

        # Delete the list
        response = await async_client.delete(
            f"/api/v1/keyword-lists/{list_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify it's deleted
        response = await async_client.get(
            f"/api/v1/keyword-lists/{list_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch("app.api.v1.keyword_lists.StorageService")
    async def test_list_keyword_lists_with_filter(
        self,
        mock_storage_class,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test listing keyword lists with pagination."""
        # Mock storage service
        mock_storage = AsyncMock()
        mock_storage.upload_file = AsyncMock(return_value="s3://test-bucket/file.csv")
        mock_storage_class.return_value = mock_storage

        # Create multiple lists
        with patch("app.api.v1.keyword_lists.process_keywords_background"):
            for i in range(3):
                await async_client.post(
                    "/api/v1/keyword-lists",
                    data={
                        "name": f"Test List {i}",
                        "workspace_id": str(test_workspace_id),
                    },
                    files={"file": ("keywords.csv", b"keyword\napple\n", "text/csv")},
                    headers=auth_headers,
                )

        # List with pagination
        response = await async_client.get(
            f"/api/v1/keyword-lists?workspace_id={test_workspace_id}&page=1&page_size=2",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["data"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
