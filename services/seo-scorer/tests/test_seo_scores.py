"""Tests for SEO Scores API endpoints."""

import pytest
from uuid import uuid4

from app.schemas.seo_score import DEFAULT_CHECKLIST


class TestSeoScoresAPI:
    """Tests for SEO Scores API."""

    @pytest.mark.asyncio
    async def test_create_seo_score(self, async_client, auth_headers, test_workspace_id):
        """Test creating an SEO score via API."""
        response = await async_client.post(
            "/api/v1/seo-scores",
            json={
                "workspace_id": str(test_workspace_id),
                "status": "pending",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["workspace_id"] == str(test_workspace_id)
        assert data["status"] == "pending"
        assert data["manual_score"] == 0
        assert data["checklist"] == DEFAULT_CHECKLIST

    @pytest.mark.asyncio
    async def test_create_seo_score_with_checklist(
        self, async_client, auth_headers, test_workspace_id
    ):
        """Test creating an SEO score with custom checklist."""
        checklist = DEFAULT_CHECKLIST.copy()
        checklist["title_contains_keyword"] = True
        checklist["h1_present"] = True

        response = await async_client.post(
            "/api/v1/seo-scores",
            json={
                "workspace_id": str(test_workspace_id),
                "checklist": checklist,
                "status": "pending",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["manual_score"] == 20  # 2/10 * 100

    @pytest.mark.asyncio
    async def test_create_seo_score_unauthorized(self, async_client, test_workspace_id):
        """Test creating SEO score without authentication."""
        response = await async_client.post(
            "/api/v1/seo-scores",
            json={
                "workspace_id": str(test_workspace_id),
                "status": "pending",
            },
        )

        # Without auth header, HTTPBearer returns 401 or 403 depending on configuration
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_list_seo_scores(self, async_client, auth_headers, test_workspace_id):
        """Test listing SEO scores."""
        # Create a score first
        await async_client.post(
            "/api/v1/seo-scores",
            json={
                "workspace_id": str(test_workspace_id),
                "status": "pending",
            },
            headers=auth_headers,
        )

        response = await async_client.get(
            f"/api/v1/seo-scores?workspace_id={test_workspace_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["data"]) == 1

    @pytest.mark.asyncio
    async def test_list_seo_scores_with_filter(
        self, async_client, auth_headers, test_workspace_id
    ):
        """Test listing SEO scores with status filter."""
        # Create scores with different statuses
        for status in ["pending", "completed"]:
            await async_client.post(
                "/api/v1/seo-scores",
                json={
                    "workspace_id": str(test_workspace_id),
                    "status": status,
                },
                headers=auth_headers,
            )

        response = await async_client.get(
            f"/api/v1/seo-scores?workspace_id={test_workspace_id}&status=completed",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["data"][0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_seo_score(self, async_client, auth_headers, test_workspace_id):
        """Test getting a specific SEO score."""
        # Create a score first
        create_response = await async_client.post(
            "/api/v1/seo-scores",
            json={
                "workspace_id": str(test_workspace_id),
                "status": "pending",
            },
            headers=auth_headers,
        )
        score_id = create_response.json()["id"]

        response = await async_client.get(
            f"/api/v1/seo-scores/{score_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == score_id

    @pytest.mark.asyncio
    async def test_get_seo_score_not_found(self, async_client, auth_headers):
        """Test getting non-existent SEO score."""
        response = await async_client.get(
            f"/api/v1/seo-scores/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_seo_score(self, async_client, auth_headers, test_workspace_id):
        """Test updating an SEO score."""
        # Create a score first
        create_response = await async_client.post(
            "/api/v1/seo-scores",
            json={
                "workspace_id": str(test_workspace_id),
                "status": "pending",
            },
            headers=auth_headers,
        )
        score_id = create_response.json()["id"]

        # Update the score
        response = await async_client.put(
            f"/api/v1/seo-scores/{score_id}",
            json={"status": "completed"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_update_seo_score_checklist(
        self, async_client, auth_headers, test_workspace_id
    ):
        """Test updating SEO score checklist recalculates score."""
        # Create a score first
        create_response = await async_client.post(
            "/api/v1/seo-scores",
            json={
                "workspace_id": str(test_workspace_id),
                "status": "pending",
            },
            headers=auth_headers,
        )
        score_id = create_response.json()["id"]
        assert create_response.json()["manual_score"] == 0

        # Update with 5 checked items
        new_checklist = DEFAULT_CHECKLIST.copy()
        for i, key in enumerate(new_checklist.keys()):
            if i < 5:
                new_checklist[key] = True

        response = await async_client.put(
            f"/api/v1/seo-scores/{score_id}",
            json={"checklist": new_checklist},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["manual_score"] == 50  # 5/10 * 100

    @pytest.mark.asyncio
    async def test_update_seo_score_not_found(self, async_client, auth_headers):
        """Test updating non-existent SEO score."""
        response = await async_client.put(
            f"/api/v1/seo-scores/{uuid4()}",
            json={"status": "completed"},
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_seo_score(self, async_client, auth_headers, test_workspace_id):
        """Test deleting an SEO score."""
        # Create a score first
        create_response = await async_client.post(
            "/api/v1/seo-scores",
            json={
                "workspace_id": str(test_workspace_id),
                "status": "pending",
            },
            headers=auth_headers,
        )
        score_id = create_response.json()["id"]

        # Delete the score
        response = await async_client.delete(
            f"/api/v1/seo-scores/{score_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify it's deleted
        get_response = await async_client.get(
            f"/api/v1/seo-scores/{score_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_seo_score_not_found(self, async_client, auth_headers):
        """Test deleting non-existent SEO score."""
        response = await async_client.delete(
            f"/api/v1/seo-scores/{uuid4()}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_calculate_score(self, async_client, auth_headers):
        """Test calculating score without saving."""
        checklist = {
            "item1": True,
            "item2": True,
            "item3": False,
            "item4": True,
        }

        response = await async_client.post(
            "/api/v1/seo-scores/calculate",
            json=checklist,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 75  # 3/4 * 100
        assert data["total_items"] == 4
        assert data["checked_items"] == 3


class TestHealthEndpoints:
    """Tests for health endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client):
        """Test health check endpoint."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "seo-scorer"

    @pytest.mark.asyncio
    async def test_readiness_check(self, async_client):
        """Test readiness check endpoint."""
        response = await async_client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "seo-scorer"
