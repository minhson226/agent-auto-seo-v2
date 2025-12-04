"""Tests for content analyzer functionality."""

import pytest
from app.analyzer import ContentAnalyzer, ContentMetrics, get_content_analyzer


class TestContentAnalyzer:
    """Tests for ContentAnalyzer class."""

    def test_init_analyzer(self):
        """Test analyzer initialization."""
        analyzer = ContentAnalyzer()
        assert analyzer is not None

    def test_extract_metrics_basic(self, mock_html_page):
        """Test basic metrics extraction from HTML."""
        analyzer = ContentAnalyzer()
        metrics = analyzer._extract_metrics("https://example.com", mock_html_page)

        assert isinstance(metrics, ContentMetrics)
        assert metrics.url == "https://example.com"
        assert metrics.h1 == "Main Heading"
        assert metrics.h2_count == 2
        assert metrics.h3_count == 1

    def test_extract_headings(self, mock_html_page):
        """Test heading extraction."""
        analyzer = ContentAnalyzer()
        metrics = analyzer._extract_metrics("https://example.com", mock_html_page)

        assert "First Section" in metrics.h2_headings
        assert "Second Section" in metrics.h2_headings
        assert "Subsection" in metrics.h3_headings

    def test_extract_images(self, mock_html_page):
        """Test image counting."""
        analyzer = ContentAnalyzer()
        metrics = analyzer._extract_metrics("https://example.com", mock_html_page)

        assert metrics.images_count == 2
        assert metrics.images_with_alt == 1  # Only image1 has alt

    def test_extract_links(self, mock_html_page):
        """Test link counting."""
        analyzer = ContentAnalyzer()
        metrics = analyzer._extract_metrics("https://example.com", mock_html_page)

        assert metrics.internal_links >= 1
        assert metrics.external_links >= 1

    def test_extract_meta_tags(self, mock_html_page):
        """Test meta tag extraction."""
        analyzer = ContentAnalyzer()
        metrics = analyzer._extract_metrics("https://example.com", mock_html_page)

        assert metrics.meta_title == "Test Page Title"
        assert metrics.meta_description == "This is a test page description."

    def test_extract_word_count(self, mock_html_page):
        """Test word count extraction."""
        analyzer = ContentAnalyzer()
        metrics = analyzer._extract_metrics("https://example.com", mock_html_page)

        assert metrics.word_count > 0

    def test_is_internal_link(self):
        """Test internal link detection."""
        analyzer = ContentAnalyzer()

        # Internal links
        assert analyzer._is_internal_link("/page", "example.com") is True
        assert analyzer._is_internal_link("https://example.com/page", "example.com") is True

        # External links
        assert analyzer._is_internal_link("https://other.com", "example.com") is False

        # Special links (not external)
        assert analyzer._is_internal_link("#section", "example.com") is False
        assert analyzer._is_internal_link("javascript:void(0)", "example.com") is False
        assert analyzer._is_internal_link("mailto:test@test.com", "example.com") is False

    def test_aggregate_metrics_empty(self):
        """Test aggregation with empty list."""
        analyzer = ContentAnalyzer()
        result = analyzer.aggregate_metrics([])

        assert result == {}

    def test_aggregate_metrics(self):
        """Test metrics aggregation."""
        analyzer = ContentAnalyzer()

        metrics_list = [
            ContentMetrics(
                url="https://example1.com",
                word_count=1000,
                h2_count=5,
                h3_count=3,
                images_count=10,
                internal_links=5,
                external_links=3,
                h2_headings=["Intro", "Features", "Conclusion"],
            ),
            ContentMetrics(
                url="https://example2.com",
                word_count=2000,
                h2_count=8,
                h3_count=4,
                images_count=15,
                internal_links=8,
                external_links=5,
                h2_headings=["Intro", "Benefits", "Conclusion"],
            ),
        ]

        result = analyzer.aggregate_metrics(metrics_list)

        assert result["count"] == 2
        assert result["avg_word_count"] == 1500
        assert result["min_word_count"] == 1000
        assert result["max_word_count"] == 2000
        assert "common_headings" in result
        # "intro" and "conclusion" appear in both
        assert len(result["common_headings"]) >= 2

    def test_get_content_analyzer_singleton(self):
        """Test singleton pattern for analyzer."""
        analyzer1 = get_content_analyzer()
        analyzer2 = get_content_analyzer()

        assert analyzer1 is analyzer2

    def test_content_metrics_dataclass(self):
        """Test ContentMetrics dataclass."""
        metrics = ContentMetrics(
            url="https://example.com",
            word_count=1500,
            h1="Test H1",
            h2_count=5,
            h3_count=3,
        )

        assert metrics.url == "https://example.com"
        assert metrics.word_count == 1500
        assert metrics.h1 == "Test H1"
        assert metrics.h2_count == 5
        assert metrics.h2_headings == []  # Default empty list
