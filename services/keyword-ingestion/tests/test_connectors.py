"""Tests for API connectors."""

import pytest

from app.connectors import AhrefsConnector, GoogleTrendsConnector, SEMrushConnector


class TestAhrefsConnector:
    """Tests for Ahrefs connector."""

    @pytest.fixture
    def connector(self):
        """Create connector instance without API key (uses mocks)."""
        return AhrefsConnector(api_key="")

    @pytest.mark.asyncio
    async def test_get_keyword_metrics_mock(self, connector):
        """Test getting keyword metrics returns mock data."""
        result = await connector.get_keyword_metrics("python programming")

        assert "search_volume" in result
        assert "keyword_difficulty" in result
        assert "cpc" in result
        assert "clicks" in result
        assert result["source"] == "ahrefs_mock"
        assert isinstance(result["search_volume"], int)
        assert result["search_volume"] > 0

    @pytest.mark.asyncio
    async def test_get_related_keywords_mock(self, connector):
        """Test getting related keywords returns mock data."""
        result = await connector.get_related_keywords("python", limit=5)

        assert isinstance(result, list)
        assert len(result) <= 5
        if result:
            assert "keyword" in result[0]
            assert "search_volume" in result[0]

    @pytest.mark.asyncio
    async def test_get_competitor_keywords_mock(self, connector):
        """Test getting competitor keywords returns mock data."""
        result = await connector.get_competitor_keywords("example.com", limit=5)

        assert isinstance(result, list)
        assert len(result) <= 5
        if result:
            assert "keyword" in result[0]
            assert "position" in result[0]

    @pytest.mark.asyncio
    async def test_keyword_metrics_deterministic(self, connector):
        """Test that mock metrics are deterministic for same keyword."""
        result1 = await connector.get_keyword_metrics("test keyword")
        result2 = await connector.get_keyword_metrics("test keyword")

        assert result1["search_volume"] == result2["search_volume"]
        assert result1["keyword_difficulty"] == result2["keyword_difficulty"]


class TestSEMrushConnector:
    """Tests for SEMrush connector."""

    @pytest.fixture
    def connector(self):
        """Create connector instance without API key (uses mocks)."""
        return SEMrushConnector(api_key="")

    @pytest.mark.asyncio
    async def test_get_keyword_overview_mock(self, connector):
        """Test getting keyword overview returns mock data."""
        result = await connector.get_keyword_overview("seo tools")

        assert "keyword" in result
        assert "search_volume" in result
        assert "cpc" in result
        assert "competition" in result
        assert result["source"] == "semrush_mock"

    @pytest.mark.asyncio
    async def test_get_related_keywords_mock(self, connector):
        """Test getting related keywords returns mock data."""
        result = await connector.get_related_keywords("marketing", limit=5)

        assert isinstance(result, list)
        assert len(result) <= 5
        if result:
            assert "keyword" in result[0]
            assert "search_volume" in result[0]
            assert "cpc" in result[0]

    @pytest.mark.asyncio
    async def test_get_keyword_difficulty_mock(self, connector):
        """Test getting keyword difficulty returns mock data."""
        result = await connector.get_keyword_difficulty("content marketing")

        assert "keyword" in result
        assert "difficulty" in result
        assert result["source"] == "semrush_mock"
        assert 0 <= result["difficulty"] <= 100


class TestGoogleTrendsConnector:
    """Tests for Google Trends connector."""

    @pytest.fixture
    def connector(self):
        """Create connector instance."""
        return GoogleTrendsConnector()

    @pytest.mark.asyncio
    async def test_get_trending_searches_mock(self, connector):
        """Test getting trending searches returns mock data."""
        result = await connector.get_trending_searches(geo="US")

        assert isinstance(result, list)
        assert len(result) > 0
        assert "keyword" in result[0]
        assert "rank" in result[0]
        assert "source" in result[0]

    @pytest.mark.asyncio
    async def test_get_interest_over_time_mock(self, connector):
        """Test getting interest over time returns mock data."""
        result = await connector.get_interest_over_time("machine learning")

        assert "keyword" in result
        assert "trend_score" in result
        assert "trend_data" in result
        assert isinstance(result["trend_data"], list)

    @pytest.mark.asyncio
    async def test_get_related_queries_mock(self, connector):
        """Test getting related queries returns mock data."""
        result = await connector.get_related_queries("data science")

        assert "top" in result
        assert "rising" in result
        assert isinstance(result["top"], list)
        assert isinstance(result["rising"], list)

    @pytest.mark.asyncio
    async def test_trending_searches_different_geo(self, connector):
        """Test trending searches for different geos."""
        result_us = await connector.get_trending_searches(geo="US")
        result_uk = await connector.get_trending_searches(geo="UK")

        # Both should return data
        assert len(result_us) > 0
        assert len(result_uk) > 0

        # Geo should be recorded
        assert result_us[0]["geo"] == "US"
        assert result_uk[0]["geo"] == "UK"
