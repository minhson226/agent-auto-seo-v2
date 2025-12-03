"""Tests for keyword processor service."""

import pytest

from app.services.keyword_processor import KeywordProcessor


class TestKeywordProcessor:
    """Tests for KeywordProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create processor instance."""
        return KeywordProcessor()

    def test_normalize_lowercase(self, processor):
        """Test normalize converts to lowercase."""
        result = processor.normalize("Hello World")
        assert result == "hello world"

    def test_normalize_trim(self, processor):
        """Test normalize trims whitespace."""
        result = processor.normalize("  hello  ")
        assert result == "hello"

    def test_normalize_extra_spaces(self, processor):
        """Test normalize removes extra spaces."""
        result = processor.normalize("hello   world")
        assert result == "hello world"

    def test_normalize_combined(self, processor):
        """Test normalize handles all cases together."""
        result = processor.normalize("  Hello   World  ")
        assert result == "hello world"

    def test_normalize_empty_string(self, processor):
        """Test normalize handles empty string."""
        result = processor.normalize("")
        assert result == ""

    def test_normalize_only_spaces(self, processor):
        """Test normalize handles string with only spaces."""
        result = processor.normalize("   ")
        assert result == ""

    def test_deduplicate_basic(self, processor):
        """Test deduplicate removes duplicates."""
        keywords = ["apple", "banana", "apple", "cherry"]
        result = processor.deduplicate(keywords)

        assert len(result) == 3
        normalized = [n for _, n in result]
        assert "apple" in normalized
        assert "banana" in normalized
        assert "cherry" in normalized

    def test_deduplicate_case_insensitive(self, processor):
        """Test deduplicate is case insensitive."""
        keywords = ["Apple", "APPLE", "apple"]
        result = processor.deduplicate(keywords)

        assert len(result) == 1
        # First occurrence is kept
        assert result[0][0] == "Apple"
        assert result[0][1] == "apple"

    def test_deduplicate_preserves_original(self, processor):
        """Test deduplicate preserves original text."""
        keywords = ["Hello World", "hello  world"]
        result = processor.deduplicate(keywords)

        assert len(result) == 1
        # Original text is preserved
        assert result[0][0] == "Hello World"
        # Normalized text is stored
        assert result[0][1] == "hello world"

    def test_deduplicate_empty_list(self, processor):
        """Test deduplicate handles empty list."""
        result = processor.deduplicate([])
        assert result == []

    def test_deduplicate_filters_empty(self, processor):
        """Test deduplicate filters empty keywords."""
        keywords = ["apple", "", "  ", "banana"]
        result = processor.deduplicate(keywords)

        assert len(result) == 2
        normalized = [n for _, n in result]
        assert "apple" in normalized
        assert "banana" in normalized

    def test_process_combines_normalize_and_deduplicate(self, processor):
        """Test process method combines normalize and deduplicate."""
        keywords = ["  Apple  ", "APPLE", "banana", "  BANANA  "]
        result = processor.process(keywords)

        assert len(result) == 2
        normalized = [n for _, n in result]
        assert "apple" in normalized
        assert "banana" in normalized

    def test_deduplicate_with_whitespace_variations(self, processor):
        """Test deduplicate handles whitespace variations as duplicates."""
        keywords = ["hello world", "hello  world", "  hello world  "]
        result = processor.deduplicate(keywords)

        assert len(result) == 1
        assert result[0][1] == "hello world"
