"""Tests for GA4 and GSC connectors."""

import pytest

from app.connectors.ga4_connector import GA4Connector
from app.connectors.gsc_connector import GSCConnector


class TestGA4Connector:
    """Tests for Google Analytics 4 connector."""

    def test_init(self):
        """Test GA4 connector initialization."""
        connector = GA4Connector(property_id="123456789")
        assert connector.property_id == "123456789"
        assert connector._mock_mode is False

    def test_enable_mock_mode(self):
        """Test enabling mock mode."""
        connector = GA4Connector(property_id="123456789")
        mock_data = [
            {
                "page_path": "/test-page",
                "page_views": 100,
                "sessions": 50,
                "avg_session_duration": 120.5,
            }
        ]
        connector.enable_mock_mode(mock_data)
        assert connector._mock_mode is True
        assert connector._mock_data == mock_data

    @pytest.mark.asyncio
    async def test_get_page_metrics_mock(self):
        """Test getting page metrics in mock mode."""
        connector = GA4Connector(property_id="123456789")
        mock_data = [
            {
                "page_path": "/article-1",
                "page_views": 500,
                "sessions": 200,
                "avg_session_duration": 180.0,
            },
            {
                "page_path": "/article-2",
                "page_views": 300,
                "sessions": 150,
                "avg_session_duration": 90.0,
            },
        ]
        connector.enable_mock_mode(mock_data)

        result = await connector.get_page_metrics("2025-01-01", "2025-01-31")

        assert len(result) == 2
        assert result[0]["page_path"] == "/article-1"
        assert result[0]["page_views"] == 500
        assert result[1]["page_path"] == "/article-2"

    @pytest.mark.asyncio
    async def test_get_page_metrics_empty_mock(self):
        """Test getting page metrics with empty mock data."""
        connector = GA4Connector(property_id="123456789")
        connector.enable_mock_mode([])

        result = await connector.get_page_metrics("2025-01-01", "2025-01-31")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_engagement_metrics_mock(self):
        """Test getting engagement metrics in mock mode."""
        connector = GA4Connector(property_id="123456789")
        connector.enable_mock_mode()

        result = await connector.get_engagement_metrics("2025-01-01", "2025-01-31")

        assert "total_users" in result
        assert "new_users" in result
        assert "engagement_rate" in result

    @pytest.mark.asyncio
    async def test_get_traffic_sources_mock(self):
        """Test getting traffic sources in mock mode."""
        connector = GA4Connector(property_id="123456789")
        connector.enable_mock_mode([])

        result = await connector.get_traffic_sources("2025-01-01", "2025-01-31")

        assert result == []


class TestGSCConnector:
    """Tests for Google Search Console connector."""

    def test_init(self):
        """Test GSC connector initialization."""
        connector = GSCConnector(site_url="https://example.com")
        assert connector.site_url == "https://example.com"
        assert connector._mock_mode is False

    def test_enable_mock_mode(self):
        """Test enabling mock mode."""
        connector = GSCConnector(site_url="https://example.com")
        mock_data = [
            {
                "page": "https://example.com/test",
                "query": "test query",
                "clicks": 100,
                "impressions": 1000,
                "ctr": 0.1,
                "position": 5.5,
            }
        ]
        connector.enable_mock_mode(mock_data)
        assert connector._mock_mode is True
        assert connector._mock_data == mock_data

    @pytest.mark.asyncio
    async def test_get_performance_data_mock(self):
        """Test getting performance data in mock mode."""
        connector = GSCConnector(site_url="https://example.com")
        mock_data = [
            {
                "page": "https://example.com/article-1",
                "query": "seo tips",
                "clicks": 50,
                "impressions": 500,
                "ctr": 0.1,
                "position": 8.2,
            },
            {
                "page": "https://example.com/article-2",
                "query": "marketing guide",
                "clicks": 30,
                "impressions": 300,
                "ctr": 0.1,
                "position": 12.5,
            },
        ]
        connector.enable_mock_mode(mock_data)

        result = await connector.get_performance_data("2025-01-01", "2025-01-31")

        assert len(result) == 2
        assert result[0]["clicks"] == 50
        assert result[1]["position"] == 12.5

    @pytest.mark.asyncio
    async def test_get_page_performance_mock(self):
        """Test getting page performance in mock mode."""
        connector = GSCConnector(site_url="https://example.com")
        mock_data = [
            {
                "page": "https://example.com/article-1",
                "clicks": 100,
                "impressions": 1000,
                "position": 5.0,
            }
        ]
        connector.enable_mock_mode(mock_data)

        result = await connector.get_page_performance("2025-01-01", "2025-01-31")

        assert len(result) == 1
        assert result[0]["page"] == "https://example.com/article-1"

    @pytest.mark.asyncio
    async def test_get_query_performance_mock(self):
        """Test getting query performance in mock mode."""
        connector = GSCConnector(site_url="https://example.com")
        connector.enable_mock_mode([])

        result = await connector.get_query_performance("2025-01-01", "2025-01-31")

        assert result == []

    @pytest.mark.asyncio
    async def test_get_daily_performance_mock(self):
        """Test getting daily performance in mock mode."""
        connector = GSCConnector(site_url="https://example.com")
        connector.enable_mock_mode([])

        result = await connector.get_daily_performance("2025-01-01", "2025-01-31")

        assert result == []
