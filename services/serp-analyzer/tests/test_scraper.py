"""Tests for SERP scraper functionality."""

import pytest
from app.scraper import SERPScraper, SERPResult, get_serp_scraper


class TestSERPScraper:
    """Tests for SERPScraper class."""

    def test_init_scraper(self):
        """Test scraper initialization."""
        scraper = SERPScraper()
        assert scraper is not None
        assert scraper.google_api_key is None or isinstance(scraper.google_api_key, str)

    def test_init_with_api_keys(self):
        """Test scraper initialization with API keys."""
        scraper = SERPScraper(
            google_api_key="test-key",
            google_cse_id="test-cse-id",
            scraper_api_key="test-scraper-key",
        )
        assert scraper.google_api_key == "test-key"
        assert scraper.google_cse_id == "test-cse-id"
        assert scraper.scraper_api_key == "test-scraper-key"

    def test_mock_results(self):
        """Test mock results generation."""
        scraper = SERPScraper()
        results = scraper._get_mock_results("test keyword", 5)

        assert len(results) == 5
        assert all(isinstance(r, SERPResult) for r in results)
        assert results[0].position == 1
        assert results[4].position == 5

    def test_mock_results_content(self):
        """Test mock results contain expected content."""
        scraper = SERPScraper()
        results = scraper._get_mock_results("python programming", 3)

        assert all("python-programming" in r.url for r in results)
        assert all(r.domain for r in results)
        assert all(r.title for r in results)

    @pytest.mark.asyncio
    async def test_get_top_results_mock(self):
        """Test getting top results returns mock data when no API keys."""
        scraper = SERPScraper()  # No API keys
        results = await scraper.get_top_results("test keyword", num_results=5)

        assert len(results) == 5
        assert all(isinstance(r, SERPResult) for r in results)

    @pytest.mark.asyncio
    async def test_get_top_results_limit(self):
        """Test result count is limited correctly."""
        scraper = SERPScraper()
        results = await scraper.get_top_results("test", num_results=3)

        assert len(results) == 3

    def test_get_serp_scraper_singleton(self):
        """Test singleton pattern for scraper."""
        scraper1 = get_serp_scraper()
        scraper2 = get_serp_scraper()

        assert scraper1 is scraper2

    def test_serp_result_dataclass(self):
        """Test SERPResult dataclass."""
        result = SERPResult(
            position=1,
            url="https://example.com/page",
            title="Test Title",
            description="Test Description",
            domain="example.com",
        )

        assert result.position == 1
        assert result.url == "https://example.com/page"
        assert result.title == "Test Title"
        assert result.description == "Test Description"
        assert result.domain == "example.com"
