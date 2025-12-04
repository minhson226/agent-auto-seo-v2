"""Tests for article API endpoints."""

from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

import pytest
from httpx import AsyncClient


class TestArticleEndpoints:
    """Tests for article API endpoints."""

    @pytest.mark.asyncio
    async def test_create_article_unauthorized(self, async_client: AsyncClient):
        """Test creating article without auth fails."""
        response = await async_client.post(
            "/api/v1/articles",
            json={
                "title": "Test Article",
                "workspace_id": str(uuid4()),
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_article(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test creating an article directly."""
        response = await async_client.post(
            "/api/v1/articles",
            json={
                "title": "Test SEO Article",
                "workspace_id": str(test_workspace_id),
                "content": "# Test Content\n\nThis is a test article.",
                "status": "draft",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test SEO Article"
        assert data["status"] == "draft"
        # Default ai_model_used should be 'gpt-3.5-turbo' when not specified
        assert data["ai_model_used"] == "gpt-3.5-turbo"
        assert data["content"] == "# Test Content\n\nThis is a test article."

    @pytest.mark.asyncio
    async def test_list_articles_unauthorized(self, async_client: AsyncClient):
        """Test listing articles without auth fails."""
        response = await async_client.get(
            f"/api/v1/articles?workspace_id={uuid4()}"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_articles_empty(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test listing articles returns empty when none exist."""
        response = await async_client.get(
            f"/api/v1/articles?workspace_id={test_workspace_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_articles(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test listing articles with pagination."""
        # Create multiple articles
        for i in range(3):
            await async_client.post(
                "/api/v1/articles",
                json={
                    "title": f"Article {i}",
                    "workspace_id": str(test_workspace_id),
                },
                headers=auth_headers,
            )

        response = await async_client.get(
            f"/api/v1/articles?workspace_id={test_workspace_id}&page=1&page_size=2",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["data"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    @pytest.mark.asyncio
    async def test_list_articles_filter_by_status(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test listing articles filtered by status."""
        # Create articles with different statuses
        await async_client.post(
            "/api/v1/articles",
            json={
                "title": "Draft Article",
                "workspace_id": str(test_workspace_id),
                "status": "draft",
            },
            headers=auth_headers,
        )
        await async_client.post(
            "/api/v1/articles",
            json={
                "title": "Published Article",
                "workspace_id": str(test_workspace_id),
                "status": "published",
            },
            headers=auth_headers,
        )

        # Filter by draft status
        response = await async_client.get(
            f"/api/v1/articles?workspace_id={test_workspace_id}&status=draft",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["status"] == "draft"

    @pytest.mark.asyncio
    async def test_get_article_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test getting non-existent article returns 404."""
        response = await async_client.get(
            f"/api/v1/articles/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_article(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test getting a specific article."""
        # Create article
        create_response = await async_client.post(
            "/api/v1/articles",
            json={
                "title": "My Article",
                "workspace_id": str(test_workspace_id),
                "content": "Article content here",
            },
            headers=auth_headers,
        )
        article_id = create_response.json()["id"]

        # Get article
        response = await async_client.get(
            f"/api/v1/articles/{article_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == article_id
        assert data["title"] == "My Article"
        assert data["content"] == "Article content here"

    @pytest.mark.asyncio
    async def test_update_article_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test updating non-existent article returns 404."""
        response = await async_client.put(
            f"/api/v1/articles/{uuid4()}",
            json={"title": "Updated Title"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_article(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test updating an article."""
        # Create article
        create_response = await async_client.post(
            "/api/v1/articles",
            json={
                "title": "Original Title",
                "workspace_id": str(test_workspace_id),
                "status": "draft",
            },
            headers=auth_headers,
        )
        article_id = create_response.json()["id"]

        # Update article
        response = await async_client.put(
            f"/api/v1/articles/{article_id}",
            json={
                "title": "Updated Title",
                "status": "published",
                "content": "Updated content",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "published"
        assert data["content"] == "Updated content"

    @pytest.mark.asyncio
    async def test_delete_article_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test deleting non-existent article returns 404."""
        response = await async_client.delete(
            f"/api/v1/articles/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_article(
        self,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test deleting an article."""
        # Create article
        create_response = await async_client.post(
            "/api/v1/articles",
            json={
                "title": "To Delete",
                "workspace_id": str(test_workspace_id),
            },
            headers=auth_headers,
        )
        article_id = create_response.json()["id"]

        # Delete article
        response = await async_client.delete(
            f"/api/v1/articles/{article_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify it's deleted
        response = await async_client.get(
            f"/api/v1/articles/{article_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestContentGeneration:
    """Tests for content generation functionality."""

    @pytest.mark.asyncio
    async def test_generate_article_plan_not_found(
        self,
        async_client: AsyncClient,
        auth_headers,
    ):
        """Test generating article with non-existent plan returns 404."""
        response = await async_client.post(
            "/api/v1/articles/generate",
            json={"plan_id": str(uuid4())},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "content-generator"

    @pytest.mark.asyncio
    async def test_readiness_check(self, async_client: AsyncClient):
        """Test readiness check endpoint."""
        response = await async_client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "content-generator"
