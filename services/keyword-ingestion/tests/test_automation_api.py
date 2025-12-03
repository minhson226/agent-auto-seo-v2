"""Tests for automation API endpoints."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient


class TestAutomationEndpoints:
    """Tests for automation API endpoints."""

    @pytest.mark.asyncio
    async def test_enrich_keywords_unauthorized(self, async_client: AsyncClient):
        """Test enrich keywords without auth fails."""
        response = await async_client.post(
            "/api/v1/keyword-lists/enrich",
            json={"list_id": str(uuid4()), "source": "ahrefs"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_from_trends_unauthorized(self, async_client: AsyncClient):
        """Test from-trends endpoint without auth fails."""
        response = await async_client.post(
            "/api/v1/keyword-lists/from-trends",
            json={"workspace_id": str(uuid4()), "geo": "US"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_from_competitor_unauthorized(self, async_client: AsyncClient):
        """Test from-competitor endpoint without auth fails."""
        response = await async_client.post(
            "/api/v1/keyword-lists/from-competitor",
            json={
                "workspace_id": str(uuid4()),
                "competitor_domain": "example.com",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_from_paste_unauthorized(self, async_client: AsyncClient):
        """Test from-paste endpoint without auth fails."""
        response = await async_client.post(
            "/api/v1/keyword-lists/from-paste",
            json={
                "workspace_id": str(uuid4()),
                "name": "Test Keywords",
                "keywords": ["keyword1", "keyword2"],
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_enrich_keywords_not_found(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test enrich keywords with non-existent list returns 404."""
        response = await async_client.post(
            "/api/v1/keyword-lists/enrich",
            json={"list_id": str(uuid4()), "source": "ahrefs"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_from_paste_success(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test pasting keywords successfully creates a list."""
        keywords = ["python tutorial", "learn python", "python for beginners"]

        response = await async_client.post(
            "/api/v1/keyword-lists/from-paste",
            json={
                "workspace_id": str(test_workspace_id),
                "name": "Pasted Keywords",
                "keywords": keywords,
                "description": "Test description",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Pasted Keywords"
        assert data["total_keywords"] == 3
        assert data["status"] == "completed"
        assert "list_id" in data

    @pytest.mark.asyncio
    async def test_from_paste_deduplicates(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test pasting keywords deduplicates them."""
        keywords = ["Python", "python", "PYTHON", "JavaScript"]

        response = await async_client.post(
            "/api/v1/keyword-lists/from-paste",
            json={
                "workspace_id": str(test_workspace_id),
                "name": "Deduped Keywords",
                "keywords": keywords,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should only have 2 unique keywords after normalization
        assert data["total_keywords"] == 2

    @pytest.mark.asyncio
    async def test_from_paste_empty_keywords(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test pasting empty keywords list fails."""
        response = await async_client.post(
            "/api/v1/keyword-lists/from-paste",
            json={
                "workspace_id": str(test_workspace_id),
                "name": "Empty Keywords",
                "keywords": [],
            },
            headers=auth_headers,
        )
        # Pydantic validation should fail with min_length=1
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_from_paste_only_whitespace(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test pasting only whitespace keywords fails."""
        response = await async_client.post(
            "/api/v1/keyword-lists/from-paste",
            json={
                "workspace_id": str(test_workspace_id),
                "name": "Whitespace Keywords",
                "keywords": ["  ", "", "   "],
            },
            headers=auth_headers,
        )
        # Should fail because all keywords are filtered out
        assert response.status_code == 400

    @pytest.mark.asyncio
    @patch("app.api.v1.automation.event_publisher")
    async def test_from_paste_publishes_event(
        self,
        mock_publisher,
        async_client: AsyncClient,
        auth_headers,
        test_workspace_id,
    ):
        """Test pasting keywords publishes an event."""
        mock_publisher.publish = AsyncMock()

        response = await async_client.post(
            "/api/v1/keyword-lists/from-paste",
            json={
                "workspace_id": str(test_workspace_id),
                "name": "Event Test",
                "keywords": ["keyword1", "keyword2"],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        # Event should have been published
        mock_publisher.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_from_trends_uses_fallback(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test from-trends endpoint returns processing status."""
        # Patch background task to avoid database issues
        with patch("app.api.v1.automation._discover_trends_background"):
            response = await async_client.post(
                "/api/v1/keyword-lists/from-trends",
                json={
                    "workspace_id": str(test_workspace_id),
                    "geo": "US",
                },
                headers=auth_headers,
            )

        # Should return processing status
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert "workspace_id" in data

    @pytest.mark.asyncio
    async def test_from_competitor_uses_fallback(
        self, async_client: AsyncClient, auth_headers, test_workspace_id
    ):
        """Test from-competitor endpoint returns processing status."""
        # Patch background task to avoid database issues
        with patch("app.api.v1.automation._pull_competitor_background"):
            response = await async_client.post(
                "/api/v1/keyword-lists/from-competitor",
                json={
                    "workspace_id": str(test_workspace_id),
                    "competitor_domain": "example.com",
                    "limit": 50,
                },
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["competitor_domain"] == "example.com"


class TestIntentEndpoints:
    """Tests for intent classification API endpoints."""

    @pytest.mark.asyncio
    async def test_classify_intent_unauthorized(self, async_client: AsyncClient):
        """Test intent classification without auth fails."""
        response = await async_client.post(
            "/api/v1/keywords/classify-intent",
            json={"keyword": "test keyword"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_classify_intent_success(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test intent classification returns valid response."""
        response = await async_client.post(
            "/api/v1/keywords/classify-intent",
            json={"keyword": "how to learn python"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["keyword"] == "how to learn python"
        assert data["intent"] == "informational"
        assert 0 <= data["confidence"] <= 100
        assert "all_scores" in data

    @pytest.mark.asyncio
    async def test_classify_intent_commercial(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test intent classification for commercial keyword."""
        response = await async_client.post(
            "/api/v1/keywords/classify-intent",
            json={"keyword": "best laptop reviews"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "commercial"

    @pytest.mark.asyncio
    async def test_classify_intent_batch_success(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test batch intent classification."""
        response = await async_client.post(
            "/api/v1/keywords/classify-intent/batch",
            json={
                "keywords": [
                    "how to cook pasta",
                    "best running shoes",
                    "buy iphone 15",
                ]
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["results"]) == 3

        # Check individual results
        intents = [r["intent"] for r in data["results"]]
        assert "informational" in intents
        assert "commercial" in intents
        assert "transactional" in intents

    @pytest.mark.asyncio
    async def test_classify_intent_batch_empty(
        self, async_client: AsyncClient, auth_headers
    ):
        """Test batch classification with empty list fails."""
        response = await async_client.post(
            "/api/v1/keywords/classify-intent/batch",
            json={"keywords": []},
            headers=auth_headers,
        )
        # Pydantic validation should fail
        assert response.status_code == 422
