"""Tests for content generator service."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.content_generator import ContentGenerator


class TestContentGenerator:
    """Tests for ContentGenerator class."""

    def test_build_prompt(self):
        """Test prompt building."""
        generator = ContentGenerator(api_key="test-key")
        prompt = generator._build_prompt(
            title="Ultimate Guide to SEO",
            target_keywords=["seo", "search engine optimization"],
            estimated_word_count=2000,
        )

        assert "Ultimate Guide to SEO" in prompt
        assert "seo, search engine optimization" in prompt
        assert "2000" in prompt
        assert "H1" in prompt
        assert "H2" in prompt
        assert "Markdown" in prompt

    def test_build_prompt_no_keywords(self):
        """Test prompt building without keywords."""
        generator = ContentGenerator(api_key="test-key")
        prompt = generator._build_prompt(
            title="Test Article",
            target_keywords=[],
            estimated_word_count=None,
        )

        assert "Test Article" in prompt
        assert "1500-2000" in prompt  # default word count

    def test_calculate_cost(self):
        """Test cost calculation."""
        generator = ContentGenerator(api_key="test-key")
        
        # 1000 input tokens + 1000 output tokens
        cost = generator._calculate_cost(1000, 1000)
        
        # Expected: (1000/1000 * 0.0015) + (1000/1000 * 0.002) = 0.0015 + 0.002 = 0.0035
        assert cost == Decimal("0.0035")

    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens."""
        generator = ContentGenerator(api_key="test-key")
        cost = generator._calculate_cost(0, 0)
        assert cost == Decimal("0")

    def test_count_words(self):
        """Test word counting."""
        generator = ContentGenerator(api_key="test-key")
        
        # Simple text
        assert generator._count_words("Hello world") == 2
        
        # Text with markdown
        text = "# Heading\n\nThis is **bold** and *italic* text."
        count = generator._count_words(text)
        assert count == 7  # Heading This is bold and italic text

    def test_count_words_empty(self):
        """Test word counting with empty text."""
        generator = ContentGenerator(api_key="test-key")
        assert generator._count_words("") == 0

    @pytest.mark.asyncio
    async def test_generate_article_no_api_key(self):
        """Test generation fails without API key."""
        generator = ContentGenerator(api_key="")
        generator.client = None  # Simulate no client

        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            await generator.generate_article(
                title="Test",
                target_keywords=[],
            )

    @pytest.mark.asyncio
    async def test_generate_article_success(self):
        """Test successful article generation."""
        # Mock OpenAI response
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 100
        mock_usage.completion_tokens = 500

        mock_message = MagicMock()
        mock_message.content = "# Test Article\n\nThis is generated content."

        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        # Create mock client
        mock_create = AsyncMock(return_value=mock_response)

        with patch.object(ContentGenerator, '__init__', lambda self, api_key: None):
            generator = ContentGenerator(api_key="test-key")
            generator.model = "gpt-3.5-turbo"
            generator.max_tokens = 2000
            generator.temperature = 0.7
            generator.client = MagicMock()
            generator.client.chat.completions.create = mock_create

            result = await generator.generate_article(
                title="Test Article",
                target_keywords=["test", "article"],
                estimated_word_count=1000,
            )

            assert result.content == "# Test Article\n\nThis is generated content."
            assert result.model == "gpt-3.5-turbo"
            assert result.tokens_used["prompt_tokens"] == 100
            assert result.tokens_used["completion_tokens"] == 500
            assert result.word_count == 6  # "Test Article This is generated content"
