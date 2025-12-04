"""Tests for content plan API endpoints."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient


class TestContentPlanEndpoints:
    """Tests for content plan API endpoints."""

    @pytest.mark.asyncio
    async def test_create_content_plan_unauthorized(self, async_client: AsyncClient):
        """Test creating content plan without auth fails."""
        response = await async_client.post(
            "/api/v1/content-plans",
            json={
                "title": "Test Plan",
                "workspace_id": str(uuid4()),
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    @patch("app.api.v1.content_plans.event_publisher")
    async def test_create_content_plan(
        self,
        mock_event_publisher,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test creating a content plan."""
        mock_event_publisher.publish = AsyncMock()

        response = await async_client.post(
            "/api/v1/content-plans",
            json={
                "title": "Ultimate Guide to SEO",
                "workspace_id": str(test_workspace_id),
                "priority": "high",
                "target_keywords": ["seo", "search engine optimization"],
                "status": "draft",
                "estimated_word_count": 2500,
                "notes": "Focus on beginner-friendly content",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Ultimate Guide to SEO"
        assert data["priority"] == "high"
        assert data["status"] == "draft"
        assert data["target_keywords"] == ["seo", "search engine optimization"]
        assert data["estimated_word_count"] == 2500

        # Verify event was published
        mock_event_publisher.publish.assert_called_once()
        call_args = mock_event_publisher.publish.call_args
        assert call_args[0][0] == "content.plan.created"

    @pytest.mark.asyncio
    @patch("app.api.v1.content_plans.event_publisher")
    async def test_create_content_plan_with_cluster(
        self,
        mock_event_publisher,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test creating a content plan linked to a cluster."""
        mock_event_publisher.publish = AsyncMock()

        # Create cluster first
        cluster_response = await async_client.post(
            "/api/v1/topic-clusters",
            json={
                "name": "SEO Cluster",
                "workspace_id": str(test_workspace_id),
                "type": "cluster",
            },
            headers=auth_headers,
        )
        cluster_id = cluster_response.json()["id"]

        # Create content plan linked to cluster
        response = await async_client.post(
            "/api/v1/content-plans",
            json={
                "title": "SEO Tips Article",
                "workspace_id": str(test_workspace_id),
                "cluster_id": cluster_id,
                "priority": "medium",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["cluster_id"] == cluster_id

    @pytest.mark.asyncio
    @patch("app.api.v1.content_plans.event_publisher")
    async def test_create_content_plan_with_competitors_data(
        self,
        mock_event_publisher,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test creating a content plan with competitor data."""
        mock_event_publisher.publish = AsyncMock()

        response = await async_client.post(
            "/api/v1/content-plans",
            json={
                "title": "Competitor Analysis Based Article",
                "workspace_id": str(test_workspace_id),
                "competitors_data": {
                    "urls": [
                        "https://competitor1.com/article",
                        "https://competitor2.com/guide",
                    ],
                    "notes": "Both competitors rank for target keywords",
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "urls" in data["competitors_data"]
        assert len(data["competitors_data"]["urls"]) == 2

    @pytest.mark.asyncio
    async def test_list_content_plans_unauthorized(self, async_client: AsyncClient):
        """Test listing content plans without auth fails."""
        response = await async_client.get(
            f"/api/v1/content-plans?workspace_id={uuid4()}"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_content_plans_empty(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test listing content plans returns empty when none exist."""
        response = await async_client.get(
            f"/api/v1/content-plans?workspace_id={test_workspace_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    @patch("app.api.v1.content_plans.event_publisher")
    async def test_list_content_plans(
        self,
        mock_event_publisher,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test listing content plans with pagination."""
        mock_event_publisher.publish = AsyncMock()

        # Create multiple plans
        for i in range(3):
            await async_client.post(
                "/api/v1/content-plans",
                json={
                    "title": f"Plan {i}",
                    "workspace_id": str(test_workspace_id),
                },
                headers=auth_headers,
            )

        response = await async_client.get(
            f"/api/v1/content-plans?workspace_id={test_workspace_id}&page=1&page_size=2",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["data"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    @pytest.mark.asyncio
    @patch("app.api.v1.content_plans.event_publisher")
    async def test_list_content_plans_filter_by_status(
        self,
        mock_event_publisher,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test listing content plans filtered by status."""
        mock_event_publisher.publish = AsyncMock()

        # Create plans with different statuses
        await async_client.post(
            "/api/v1/content-plans",
            json={
                "title": "Draft Plan",
                "workspace_id": str(test_workspace_id),
                "status": "draft",
            },
            headers=auth_headers,
        )
        await async_client.post(
            "/api/v1/content-plans",
            json={
                "title": "Approved Plan",
                "workspace_id": str(test_workspace_id),
                "status": "approved",
            },
            headers=auth_headers,
        )

        # Filter by draft status
        response = await async_client.get(
            f"/api/v1/content-plans?workspace_id={test_workspace_id}&status=draft",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["status"] == "draft"

    @pytest.mark.asyncio
    @patch("app.api.v1.content_plans.event_publisher")
    async def test_list_content_plans_filter_by_priority(
        self,
        mock_event_publisher,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test listing content plans filtered by priority."""
        mock_event_publisher.publish = AsyncMock()

        # Create plans with different priorities
        await async_client.post(
            "/api/v1/content-plans",
            json={
                "title": "High Priority Plan",
                "workspace_id": str(test_workspace_id),
                "priority": "high",
            },
            headers=auth_headers,
        )
        await async_client.post(
            "/api/v1/content-plans",
            json={
                "title": "Low Priority Plan",
                "workspace_id": str(test_workspace_id),
                "priority": "low",
            },
            headers=auth_headers,
        )

        # Filter by high priority
        response = await async_client.get(
            f"/api/v1/content-plans?workspace_id={test_workspace_id}&priority=high",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_get_content_plan_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test getting non-existent content plan returns 404."""
        response = await async_client.get(
            f"/api/v1/content-plans/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch("app.api.v1.content_plans.event_publisher")
    async def test_get_content_plan(
        self,
        mock_event_publisher,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test getting a specific content plan."""
        mock_event_publisher.publish = AsyncMock()

        # Create plan
        create_response = await async_client.post(
            "/api/v1/content-plans",
            json={
                "title": "My Content Plan",
                "workspace_id": str(test_workspace_id),
            },
            headers=auth_headers,
        )
        plan_id = create_response.json()["id"]

        # Get plan
        response = await async_client.get(
            f"/api/v1/content-plans/{plan_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == plan_id
        assert data["title"] == "My Content Plan"

    @pytest.mark.asyncio
    async def test_update_content_plan_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test updating non-existent content plan returns 404."""
        response = await async_client.put(
            f"/api/v1/content-plans/{uuid4()}",
            json={"title": "Updated Title"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch("app.api.v1.content_plans.event_publisher")
    async def test_update_content_plan(
        self,
        mock_event_publisher,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test updating a content plan."""
        mock_event_publisher.publish = AsyncMock()

        # Create plan
        create_response = await async_client.post(
            "/api/v1/content-plans",
            json={
                "title": "Original Title",
                "workspace_id": str(test_workspace_id),
                "priority": "low",
                "status": "draft",
            },
            headers=auth_headers,
        )
        plan_id = create_response.json()["id"]

        # Update plan
        response = await async_client.put(
            f"/api/v1/content-plans/{plan_id}",
            json={
                "title": "Updated Title",
                "priority": "high",
                "status": "approved",
                "notes": "Reviewed and approved",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["priority"] == "high"
        assert data["status"] == "approved"
        assert data["notes"] == "Reviewed and approved"

    @pytest.mark.asyncio
    async def test_delete_content_plan_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test deleting non-existent content plan returns 404."""
        response = await async_client.delete(
            f"/api/v1/content-plans/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch("app.api.v1.content_plans.event_publisher")
    async def test_delete_content_plan(
        self,
        mock_event_publisher,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test deleting a content plan."""
        mock_event_publisher.publish = AsyncMock()

        # Create plan
        create_response = await async_client.post(
            "/api/v1/content-plans",
            json={
                "title": "To Delete",
                "workspace_id": str(test_workspace_id),
            },
            headers=auth_headers,
        )
        plan_id = create_response.json()["id"]

        # Delete plan
        response = await async_client.delete(
            f"/api/v1/content-plans/{plan_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify it's deleted
        response = await async_client.get(
            f"/api/v1/content-plans/{plan_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404
