"""Tests for content generator service."""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.content_generator import ContentGenerator
from app.services.event_publisher import EventPublisher
from app.services.image_storage import ImageStorageService


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
    async def test_generate_article_no_api_key_returns_mock(self):
        """Test generation returns mock content without API key.

        When no API key is configured, the ContentGenerator should return
        mock content instead of failing. This allows tests to run in CI
        without real API credentials.
        """
        generator = ContentGenerator(api_key="")

        result = await generator.generate_article(
            title="Test Article",
            target_keywords=["seo", "content"],
        )

        # Should return mock content, not raise an error
        assert result.content is not None
        assert "Test Article" in result.content
        assert "-mock" in result.model  # Model name should indicate mock
        assert result.word_count > 0
        assert result.cost_usd >= Decimal("0")
        assert "prompt_tokens" in result.tokens_used
        assert "completion_tokens" in result.tokens_used

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


class TestEventPublisherMock:
    """Tests for EventPublisher mock mode functionality."""

    @pytest.mark.asyncio
    async def test_mock_mode_initialization(self):
        """Test EventPublisher initializes in mock mode correctly."""
        publisher = EventPublisher(mock_mode=True)
        assert publisher.mock_mode is True
        assert publisher.published_events == []

    @pytest.mark.asyncio
    async def test_mock_connect_does_not_fail(self):
        """Test that connect() doesn't fail in mock mode."""
        publisher = EventPublisher(mock_mode=True)
        await publisher.connect()  # Should not raise
        assert publisher.mock_mode is True

    @pytest.mark.asyncio
    async def test_mock_publish_stores_events(self):
        """Test that publish stores events in mock mode."""
        publisher = EventPublisher(mock_mode=True)
        await publisher.connect()

        workspace_id = uuid4()
        await publisher.publish(
            "article.generated",
            {"article_id": str(uuid4()), "title": "Test Article"},
            workspace_id=workspace_id,
        )

        assert len(publisher.published_events) == 1
        event = publisher.published_events[0]
        assert event["event_type"] == "article.generated"
        assert event["workspace_id"] == str(workspace_id)
        assert "article_id" in event["payload"]
        assert event["payload"]["title"] == "Test Article"

    @pytest.mark.asyncio
    async def test_mock_clear_events(self):
        """Test clearing published events."""
        publisher = EventPublisher(mock_mode=True)
        await publisher.publish("test.event", {"key": "value"})
        assert len(publisher.published_events) == 1

        publisher.clear_events()
        assert len(publisher.published_events) == 0

    @pytest.mark.asyncio
    async def test_mock_disconnect_does_not_fail(self):
        """Test that disconnect() doesn't fail in mock mode."""
        publisher = EventPublisher(mock_mode=True)
        await publisher.connect()
        await publisher.disconnect()  # Should not raise


class TestImageStorageMock:
    """Tests for ImageStorageService mock mode functionality."""

    @pytest.mark.asyncio
    async def test_mock_mode_initialization(self):
        """Test ImageStorageService initializes in mock mode correctly."""
        storage = ImageStorageService(mock_mode=True)
        assert storage.mock_mode is True
        assert storage.mock_storage == {}

    @pytest.mark.asyncio
    async def test_mock_upload_stores_image(self):
        """Test that upload stores image in mock mode."""
        storage = ImageStorageService(mock_mode=True)
        article_id = uuid4()
        content = b"fake image content"

        path = await storage.upload_image(
            article_id=article_id,
            file_content=content,
            original_filename="test.jpg",
            content_type="image/jpeg",
        )

        assert path.startswith(f"articles/{article_id}/")
        assert path.endswith(".jpg")
        assert storage.mock_storage[path] == content

    @pytest.mark.asyncio
    async def test_mock_delete_removes_image(self):
        """Test that delete removes image in mock mode."""
        storage = ImageStorageService(mock_mode=True)
        article_id = uuid4()

        # Upload first
        path = await storage.upload_image(
            article_id=article_id,
            file_content=b"content",
            original_filename="test.png",
            content_type="image/png",
        )
        assert path in storage.mock_storage

        # Delete
        result = await storage.delete_image(path)
        assert result is True
        assert path not in storage.mock_storage

    @pytest.mark.asyncio
    async def test_mock_delete_nonexistent_returns_false(self):
        """Test that deleting non-existent image returns False."""
        storage = ImageStorageService(mock_mode=True)
        result = await storage.delete_image("nonexistent/path.jpg")
        assert result is False

    @pytest.mark.asyncio
    async def test_mock_get_image_url_returns_mock_url(self):
        """Test that get_image_url returns mock URL."""
        storage = ImageStorageService(mock_mode=True)
        url = await storage.get_image_url("articles/123/image.jpg", expires_in=3600)

        assert url.startswith("mock://storage/")
        assert "articles/123/image.jpg" in url
        assert "expires=3600" in url

    @pytest.mark.asyncio
    async def test_mock_ensure_bucket_exists_does_not_fail(self):
        """Test that ensure_bucket_exists doesn't fail in mock mode."""
        storage = ImageStorageService(mock_mode=True)
        await storage.ensure_bucket_exists()  # Should not raise

    @pytest.mark.asyncio
    async def test_mock_clear_storage(self):
        """Test clearing mock storage."""
        storage = ImageStorageService(mock_mode=True)

        # Upload some images
        await storage.upload_image(
            article_id=uuid4(),
            file_content=b"content1",
            original_filename="test1.jpg",
            content_type="image/jpeg",
        )
        await storage.upload_image(
            article_id=uuid4(),
            file_content=b"content2",
            original_filename="test2.jpg",
            content_type="image/jpeg",
        )
        assert len(storage.mock_storage) == 2

        storage.clear_storage()
        assert len(storage.mock_storage) == 0
