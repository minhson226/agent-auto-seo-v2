"""Tests for analytics API endpoints."""

from datetime import date, timedelta

import pytest


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "analytics"

    def test_ready_check(self, client):
        """Test readiness check endpoint."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "analytics"


class TestPerformanceEndpoint:
    """Tests for performance data entry endpoint."""

    def test_record_performance_success(self, client):
        """Test recording performance data successfully."""
        data = {
            "url": "https://example.com/article",
            "date": str(date.today()),
            "impressions": 1000,
            "clicks": 50,
            "position": 5.2,
            "workspace_id": "test-workspace-id",
            "article_id": "test-article-id",
        }
        response = client.post("/api/v1/analytics/performance", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["message"] == "Performance data recorded successfully"
        assert "url_hash" in result

    def test_record_performance_minimal_data(self, client):
        """Test recording performance data with minimal required fields."""
        data = {
            "url": "https://example.com/article",
            "date": str(date.today()),
            "impressions": 100,
            "clicks": 10,
            "position": 3.0,
        }
        response = client.post("/api/v1/analytics/performance", json=data)
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True

    def test_record_performance_invalid_data(self, client):
        """Test recording performance data with invalid data."""
        data = {
            "url": "https://example.com/article",
            "date": str(date.today()),
            "impressions": -1,  # Invalid: negative value
            "clicks": 10,
            "position": 3.0,
        }
        response = client.post("/api/v1/analytics/performance", json=data)
        assert response.status_code == 422  # Validation error

    def test_record_performance_missing_required_fields(self, client):
        """Test recording performance data with missing required fields."""
        data = {
            "url": "https://example.com/article",
            # Missing required fields: date, impressions, clicks, position
        }
        response = client.post("/api/v1/analytics/performance", json=data)
        assert response.status_code == 422  # Validation error


class TestSummaryEndpoint:
    """Tests for performance summary endpoint."""

    def test_get_summary_empty(self, client):
        """Test getting summary when no data exists."""
        response = client.get(
            "/api/v1/analytics/summary",
            params={"workspace_id": "test-workspace-id"},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["total_impressions"] == 0
        assert result["total_clicks"] == 0
        assert result["avg_position"] == 0.0
        assert result["articles_ranking"] == 0
        assert result["top_articles"] == []

    def test_get_summary_with_data(self, client):
        """Test getting summary with existing data."""
        # First, insert some performance data
        today = date.today()
        for i in range(3):
            data = {
                "url": f"https://example.com/article-{i}",
                "date": str(today - timedelta(days=i)),
                "impressions": 100 * (i + 1),
                "clicks": 10 * (i + 1),
                "position": 5.0 + i,
                "workspace_id": "test-workspace-id",
                "article_id": f"article-{i}",
            }
            response = client.post("/api/v1/analytics/performance", json=data)
            assert response.status_code == 200

        # Now get summary
        response = client.get(
            "/api/v1/analytics/summary",
            params={
                "workspace_id": "test-workspace-id",
                "date_from": str(today - timedelta(days=30)),
                "date_to": str(today),
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert result["total_impressions"] == 600  # 100 + 200 + 300
        assert result["total_clicks"] == 60  # 10 + 20 + 30
        assert result["avg_position"] == 6.0  # (5.0 + 6.0 + 7.0) / 3
        assert result["articles_ranking"] == 3

    def test_get_summary_missing_workspace_id(self, client):
        """Test getting summary without workspace_id."""
        response = client.get("/api/v1/analytics/summary")
        assert response.status_code == 422  # Validation error

    def test_get_summary_with_custom_date_range(self, client):
        """Test getting summary with custom date range."""
        today = date.today()
        response = client.get(
            "/api/v1/analytics/summary",
            params={
                "workspace_id": "test-workspace-id",
                "date_from": str(today - timedelta(days=7)),
                "date_to": str(today),
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert result["date_from"] == str(today - timedelta(days=7))
        assert result["date_to"] == str(today)


class TestArticlePerformanceEndpoint:
    """Tests for article performance endpoint."""

    def test_get_article_performance_empty(self, client):
        """Test getting article performance when no data exists."""
        response = client.get("/api/v1/analytics/articles/test-article-id/performance")
        assert response.status_code == 200
        result = response.json()
        assert result["article_id"] == "test-article-id"
        assert result["data"] == []

    def test_get_article_performance_with_data(self, client):
        """Test getting article performance with existing data."""
        # First, insert some performance data
        today = date.today()
        for i in range(5):
            data = {
                "url": "https://example.com/test-article",
                "date": str(today - timedelta(days=i)),
                "impressions": 100 + i * 10,
                "clicks": 10 + i,
                "position": 5.0 - i * 0.5,
                "workspace_id": "test-workspace-id",
                "article_id": "test-article-id",
            }
            response = client.post("/api/v1/analytics/performance", json=data)
            assert response.status_code == 200

        # Now get article performance
        response = client.get("/api/v1/analytics/articles/test-article-id/performance")
        assert response.status_code == 200
        result = response.json()
        assert result["article_id"] == "test-article-id"
        assert len(result["data"]) == 5

    def test_get_article_performance_custom_days(self, client):
        """Test getting article performance with custom days parameter."""
        response = client.get(
            "/api/v1/analytics/articles/test-article-id/performance",
            params={"days": 7},
        )
        assert response.status_code == 200

    def test_get_article_performance_invalid_days(self, client):
        """Test getting article performance with invalid days parameter."""
        response = client.get(
            "/api/v1/analytics/articles/test-article-id/performance",
            params={"days": 0},
        )
        assert response.status_code == 422  # Validation error

        response = client.get(
            "/api/v1/analytics/articles/test-article-id/performance",
            params={"days": 400},
        )
        assert response.status_code == 422  # Validation error


class TestClickHouseClient:
    """Tests for ClickHouse client functionality."""

    def test_url_hash(self):
        """Test URL hash generation."""
        from app.db.clickhouse import ClickHouseClient

        client = ClickHouseClient()
        url = "https://example.com/article"
        hash1 = client.url_hash(url)
        hash2 = client.url_hash(url)

        # Same URL should produce same hash
        assert hash1 == hash2

        # Different URL should produce different hash
        different_url = "https://example.com/different-article"
        different_hash = client.url_hash(different_url)
        assert hash1 != different_hash
