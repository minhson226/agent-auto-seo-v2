"""Tests for ML automation API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


class TestMLAutomationEndpoints:
    """Tests for ML automation API endpoints."""

    @pytest.mark.asyncio
    async def test_cluster_tfidf_unauthorized(self, async_client: AsyncClient):
        """Test TF-IDF clustering without auth returns 401."""
        response = await async_client.post(
            "/api/v1/ml/cluster/tfidf",
            json={"keywords": ["test", "keyword"]},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_cluster_tfidf(self, async_client: AsyncClient, auth_headers: dict):
        """Test TF-IDF clustering endpoint."""
        response = await async_client.post(
            "/api/v1/ml/cluster/tfidf",
            json={
                "keywords": [
                    "python tutorial",
                    "learn python",
                    "python basics",
                    "javascript guide",
                    "react tutorial",
                    "nodejs intro",
                ],
                "n_clusters": 2,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "labels" in data
        assert "clusters" in data
        assert len(data["labels"]) == 6

    @pytest.mark.asyncio
    async def test_cluster_tfidf_validation_error(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test TF-IDF clustering with invalid input."""
        response = await async_client.post(
            "/api/v1/ml/cluster/tfidf",
            json={
                "keywords": ["only_one"],  # Needs at least 2
                "n_clusters": 2,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_cluster_semantic_unauthorized(self, async_client: AsyncClient):
        """Test semantic clustering without auth returns 401."""
        response = await async_client.post(
            "/api/v1/ml/cluster/semantic",
            json={"keywords": ["test", "keyword"]},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_cluster_semantic(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test semantic clustering endpoint."""
        response = await async_client.post(
            "/api/v1/ml/cluster/semantic",
            json={
                "keywords": [
                    "machine learning",
                    "deep learning",
                    "artificial intelligence",
                    "cooking recipes",
                    "baking tips",
                ],
                "threshold": 0.3,
                "min_samples": 2,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "labels" in data
        assert "clusters" in data

    @pytest.mark.asyncio
    async def test_similar_keywords_unauthorized(self, async_client: AsyncClient):
        """Test similar keywords without auth returns 401."""
        response = await async_client.post(
            "/api/v1/ml/similar-keywords",
            json={"query": "test", "keywords": ["test1", "test2"]},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_similar_keywords(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test similar keywords endpoint."""
        response = await async_client.post(
            "/api/v1/ml/similar-keywords",
            json={
                "query": "python programming",
                "keywords": [
                    "learn python",
                    "python tutorial",
                    "javascript basics",
                    "react framework",
                ],
                "top_k": 3,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "similar" in data

    @pytest.mark.asyncio
    async def test_predict_ranking_unauthorized(self, async_client: AsyncClient):
        """Test ranking prediction without auth returns 401."""
        response = await async_client.post(
            "/api/v1/ml/predict-ranking",
            json={"keyword_difficulty": 50},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_predict_ranking(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test ranking prediction endpoint."""
        response = await async_client.post(
            "/api/v1/ml/predict-ranking",
            json={
                "keyword_difficulty": 30,
                "search_volume": 1000,
                "competition": 0.3,
                "content_word_count": 2000,
                "domain_authority": 50,
                "backlink_count": 10,
                "content_quality_score": 80,
                "avg_competitor_word_count": 1500,
                "avg_competitor_da": 40,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "probability" in data
        assert "prediction" in data
        assert "will_rank" in data
        assert "confidence" in data
        assert 0 <= data["probability"] <= 1

    @pytest.mark.asyncio
    async def test_generate_content_plan_unauthorized(self, async_client: AsyncClient):
        """Test content plan generation without auth returns 401."""
        response = await async_client.post(
            "/api/v1/ml/generate-content-plan",
            json={
                "cluster_id": str(uuid4()),
                "workspace_id": str(uuid4()),
                "keywords": ["test"],
                "primary_keyword": "test",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_generate_content_plan(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test content plan generation endpoint."""
        cluster_id = uuid4()
        workspace_id = uuid4()

        response = await async_client.post(
            "/api/v1/ml/generate-content-plan",
            json={
                "cluster_id": str(cluster_id),
                "workspace_id": str(workspace_id),
                "keywords": ["python tutorial", "learn python", "python basics"],
                "primary_keyword": "python tutorial",
                "keyword_difficulty": 40,
                "search_volume": 1500,
                "competition": 0.4,
                "competitor_avg_word_count": 2000,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "title" in data
        assert "priority" in data
        assert "estimated_word_count" in data
        assert "outline" in data
        assert "seo_recommendations" in data
        assert data["status"] == "draft"

    @pytest.mark.asyncio
    async def test_feature_importance_unauthorized(self, async_client: AsyncClient):
        """Test feature importance without auth returns 401."""
        response = await async_client.get("/api/v1/ml/feature-importance")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_feature_importance(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Test feature importance endpoint."""
        response = await async_client.get(
            "/api/v1/ml/feature-importance",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "feature_names" in data
