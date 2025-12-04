"""Tests for topic cluster API endpoints."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient


class TestTopicClusterEndpoints:
    """Tests for topic cluster API endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "seo-strategy"

    @pytest.mark.asyncio
    async def test_readiness_check(self, async_client: AsyncClient):
        """Test readiness check endpoint."""
        response = await async_client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"

    @pytest.mark.asyncio
    async def test_create_topic_cluster_unauthorized(self, async_client: AsyncClient):
        """Test creating topic cluster without auth fails."""
        response = await async_client.post(
            "/api/v1/topic-clusters",
            json={
                "name": "Test Cluster",
                "workspace_id": str(uuid4()),
                "type": "cluster",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_topic_cluster(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test creating a topic cluster."""
        response = await async_client.post(
            "/api/v1/topic-clusters",
            json={
                "name": "SEO Best Practices",
                "workspace_id": str(test_workspace_id),
                "type": "pillar",
                "description": "Main topic for SEO strategies",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "SEO Best Practices"
        assert data["type"] == "pillar"
        assert data["workspace_id"] == str(test_workspace_id)
        assert data["description"] == "Main topic for SEO strategies"
        assert data["keyword_count"] == 0

    @pytest.mark.asyncio
    async def test_create_child_cluster(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test creating a child cluster linked to a pillar."""
        # Create pillar cluster first
        pillar_response = await async_client.post(
            "/api/v1/topic-clusters",
            json={
                "name": "Content Marketing",
                "workspace_id": str(test_workspace_id),
                "type": "pillar",
            },
            headers=auth_headers,
        )
        assert pillar_response.status_code == 201
        pillar_id = pillar_response.json()["id"]

        # Create child cluster
        response = await async_client.post(
            "/api/v1/topic-clusters",
            json={
                "name": "Blog Posts",
                "workspace_id": str(test_workspace_id),
                "type": "cluster",
                "pillar_cluster_id": pillar_id,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Blog Posts"
        assert data["type"] == "cluster"
        assert data["pillar_cluster_id"] == pillar_id

    @pytest.mark.asyncio
    async def test_list_topic_clusters_unauthorized(self, async_client: AsyncClient):
        """Test listing topic clusters without auth fails."""
        response = await async_client.get(
            f"/api/v1/topic-clusters?workspace_id={uuid4()}"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_topic_clusters_empty(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test listing topic clusters returns empty when none exist."""
        response = await async_client.get(
            f"/api/v1/topic-clusters?workspace_id={test_workspace_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_topic_clusters(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test listing topic clusters with pagination."""
        # Create multiple clusters
        for i in range(3):
            await async_client.post(
                "/api/v1/topic-clusters",
                json={
                    "name": f"Cluster {i}",
                    "workspace_id": str(test_workspace_id),
                    "type": "cluster",
                },
                headers=auth_headers,
            )

        response = await async_client.get(
            f"/api/v1/topic-clusters?workspace_id={test_workspace_id}&page=1&page_size=2",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["data"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    @pytest.mark.asyncio
    async def test_list_topic_clusters_filter_by_type(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test listing topic clusters filtered by type."""
        # Create pillar and cluster types
        await async_client.post(
            "/api/v1/topic-clusters",
            json={
                "name": "Pillar 1",
                "workspace_id": str(test_workspace_id),
                "type": "pillar",
            },
            headers=auth_headers,
        )
        await async_client.post(
            "/api/v1/topic-clusters",
            json={
                "name": "Cluster 1",
                "workspace_id": str(test_workspace_id),
                "type": "cluster",
            },
            headers=auth_headers,
        )

        # Filter by pillar type
        response = await async_client.get(
            f"/api/v1/topic-clusters?workspace_id={test_workspace_id}&type=pillar",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["type"] == "pillar"

    @pytest.mark.asyncio
    async def test_get_topic_cluster_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test getting non-existent topic cluster returns 404."""
        response = await async_client.get(
            f"/api/v1/topic-clusters/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_topic_cluster(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test getting a specific topic cluster."""
        # Create cluster
        create_response = await async_client.post(
            "/api/v1/topic-clusters",
            json={
                "name": "My Cluster",
                "workspace_id": str(test_workspace_id),
                "type": "cluster",
            },
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        cluster_id = create_response.json()["id"]

        # Get cluster
        response = await async_client.get(
            f"/api/v1/topic-clusters/{cluster_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == cluster_id
        assert data["name"] == "My Cluster"

    @pytest.mark.asyncio
    async def test_update_topic_cluster_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test updating non-existent topic cluster returns 404."""
        response = await async_client.put(
            f"/api/v1/topic-clusters/{uuid4()}",
            json={"name": "Updated Name"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_topic_cluster(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test updating a topic cluster."""
        # Create cluster
        create_response = await async_client.post(
            "/api/v1/topic-clusters",
            json={
                "name": "Original Name",
                "workspace_id": str(test_workspace_id),
                "type": "cluster",
            },
            headers=auth_headers,
        )
        cluster_id = create_response.json()["id"]

        # Update cluster
        response = await async_client.put(
            f"/api/v1/topic-clusters/{cluster_id}",
            json={
                "name": "Updated Name",
                "description": "New description",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "New description"

    @pytest.mark.asyncio
    async def test_delete_topic_cluster_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test deleting non-existent topic cluster returns 404."""
        response = await async_client.delete(
            f"/api/v1/topic-clusters/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_topic_cluster(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test deleting a topic cluster."""
        # Create cluster
        create_response = await async_client.post(
            "/api/v1/topic-clusters",
            json={
                "name": "To Delete",
                "workspace_id": str(test_workspace_id),
                "type": "cluster",
            },
            headers=auth_headers,
        )
        cluster_id = create_response.json()["id"]

        # Delete cluster
        response = await async_client.delete(
            f"/api/v1/topic-clusters/{cluster_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify it's deleted
        response = await async_client.get(
            f"/api/v1/topic-clusters/{cluster_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestClusterKeywordEndpoints:
    """Tests for cluster keyword API endpoints."""

    @pytest.mark.asyncio
    async def test_add_keyword_to_cluster_cluster_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test adding keyword to non-existent cluster fails."""
        response = await async_client.post(
            f"/api/v1/topic-clusters/{uuid4()}/keywords",
            json={"keyword_id": str(uuid4())},
            headers=auth_headers,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_add_keyword_to_cluster(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test adding a keyword to a cluster."""
        # Create cluster
        create_response = await async_client.post(
            "/api/v1/topic-clusters",
            json={
                "name": "Keywords Cluster",
                "workspace_id": str(test_workspace_id),
                "type": "cluster",
            },
            headers=auth_headers,
        )
        cluster_id = create_response.json()["id"]
        keyword_id = uuid4()

        # Add keyword
        response = await async_client.post(
            f"/api/v1/topic-clusters/{cluster_id}/keywords",
            json={"keyword_id": str(keyword_id), "is_primary": True},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["cluster_id"] == cluster_id
        assert data["keyword_id"] == str(keyword_id)
        assert data["is_primary"] is True

    @pytest.mark.asyncio
    async def test_add_duplicate_keyword_to_cluster(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test adding duplicate keyword to cluster fails."""
        # Create cluster
        create_response = await async_client.post(
            "/api/v1/topic-clusters",
            json={
                "name": "Dupe Cluster",
                "workspace_id": str(test_workspace_id),
                "type": "cluster",
            },
            headers=auth_headers,
        )
        cluster_id = create_response.json()["id"]
        keyword_id = uuid4()

        # Add keyword first time
        await async_client.post(
            f"/api/v1/topic-clusters/{cluster_id}/keywords",
            json={"keyword_id": str(keyword_id)},
            headers=auth_headers,
        )

        # Add same keyword again
        response = await async_client.post(
            f"/api/v1/topic-clusters/{cluster_id}/keywords",
            json={"keyword_id": str(keyword_id)},
            headers=auth_headers,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_add_keywords_batch_to_cluster(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test adding multiple keywords to a cluster."""
        # Create cluster
        create_response = await async_client.post(
            "/api/v1/topic-clusters",
            json={
                "name": "Batch Cluster",
                "workspace_id": str(test_workspace_id),
                "type": "cluster",
            },
            headers=auth_headers,
        )
        cluster_id = create_response.json()["id"]
        keyword_ids = [str(uuid4()) for _ in range(3)]

        # Add keywords batch
        response = await async_client.post(
            f"/api/v1/topic-clusters/{cluster_id}/keywords/batch",
            json={"keyword_ids": keyword_ids},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 3

    @pytest.mark.asyncio
    async def test_remove_keyword_from_cluster(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test removing a keyword from a cluster."""
        # Create cluster
        create_response = await async_client.post(
            "/api/v1/topic-clusters",
            json={
                "name": "Remove Cluster",
                "workspace_id": str(test_workspace_id),
                "type": "cluster",
            },
            headers=auth_headers,
        )
        cluster_id = create_response.json()["id"]
        keyword_id = uuid4()

        # Add keyword
        await async_client.post(
            f"/api/v1/topic-clusters/{cluster_id}/keywords",
            json={"keyword_id": str(keyword_id)},
            headers=auth_headers,
        )

        # Remove keyword
        response = await async_client.delete(
            f"/api/v1/topic-clusters/{cluster_id}/keywords/{keyword_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_remove_keyword_not_in_cluster(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test removing keyword not in cluster returns 404."""
        # Create cluster
        create_response = await async_client.post(
            "/api/v1/topic-clusters",
            json={
                "name": "Empty Cluster",
                "workspace_id": str(test_workspace_id),
                "type": "cluster",
            },
            headers=auth_headers,
        )
        cluster_id = create_response.json()["id"]

        response = await async_client.delete(
            f"/api/v1/topic-clusters/{cluster_id}/keywords/{uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_cluster_keywords(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test listing keywords in a cluster."""
        # Create cluster
        create_response = await async_client.post(
            "/api/v1/topic-clusters",
            json={
                "name": "List Cluster",
                "workspace_id": str(test_workspace_id),
                "type": "cluster",
            },
            headers=auth_headers,
        )
        cluster_id = create_response.json()["id"]

        # Add keywords
        keyword_ids = [str(uuid4()) for _ in range(2)]
        for keyword_id in keyword_ids:
            await async_client.post(
                f"/api/v1/topic-clusters/{cluster_id}/keywords",
                json={"keyword_id": keyword_id},
                headers=auth_headers,
            )

        # List keywords
        response = await async_client.get(
            f"/api/v1/topic-clusters/{cluster_id}/keywords",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_list_cluster_keywords_cluster_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test listing keywords for non-existent cluster returns 404."""
        response = await async_client.get(
            f"/api/v1/topic-clusters/{uuid4()}/keywords",
            headers=auth_headers,
        )
        assert response.status_code == 404
