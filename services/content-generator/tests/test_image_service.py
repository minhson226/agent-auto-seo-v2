"""Tests for Image Service functionality."""

from decimal import Decimal
from urllib.parse import quote_plus

import pytest

from app.services.image_generator import ImageService, ImageResult


class TestImageService:
    """Tests for ImageService class."""

    def test_initialization(self):
        """Test image service initialization."""
        service = ImageService(mock_mode=True)
        assert service.mock_mode is True

    def test_mock_mode_detection(self):
        """Test mock mode detection."""
        # Without API keys, should work in mock mode
        service = ImageService(mock_mode=False)
        # Will work but may return mock images if no API keys

    @pytest.mark.asyncio
    async def test_get_free_images_mock(self):
        """Test getting free images in mock mode."""
        service = ImageService(mock_mode=True)

        images = await service.get_free_images(
            query="nature landscape",
            count=5,
            orientation="landscape",
        )

        assert len(images) == 5
        for image in images:
            assert image.url is not None
            assert image.source == "pexels-mock"
            assert image.width > 0
            assert image.height > 0
            assert image.alt_text is not None
            assert image.cost_usd == Decimal("0")

    @pytest.mark.asyncio
    async def test_get_free_images_count_limit(self):
        """Test image count limit is respected."""
        service = ImageService(mock_mode=True)

        images = await service.get_free_images(
            query="test",
            count=3,
        )

        assert len(images) == 3

    @pytest.mark.asyncio
    async def test_get_free_images_query_in_url(self):
        """Test query is included in mock URL."""
        service = ImageService(mock_mode=True)

        query = "beautiful sunset"
        images = await service.get_free_images(
            query=query,
            count=1,
        )

        assert quote_plus(query) in images[0].url

    @pytest.mark.asyncio
    async def test_generate_ai_image_mock(self):
        """Test AI image generation in mock mode."""
        service = ImageService(mock_mode=True)

        image = await service.generate_ai_image(
            prompt="A beautiful landscape with mountains",
            size="1024x1024",
            quality="standard",
        )

        assert image is not None
        assert image.source == "dalle-mock"
        assert image.width == 1024
        assert image.height == 1024
        assert image.cost_usd == Decimal("0.04")

    @pytest.mark.asyncio
    async def test_generate_ai_image_different_sizes(self):
        """Test AI image generation with different sizes."""
        service = ImageService(mock_mode=True)

        # Test landscape
        image = await service.generate_ai_image(
            prompt="Test",
            size="1792x1024",
        )
        assert image.width == 1792
        assert image.height == 1024

        # Test portrait
        image = await service.generate_ai_image(
            prompt="Test",
            size="1024x1792",
        )
        assert image.width == 1024
        assert image.height == 1792

    @pytest.mark.asyncio
    async def test_image_result_metadata(self):
        """Test image result contains metadata."""
        service = ImageService(mock_mode=True)

        image = await service.generate_ai_image(
            prompt="Test prompt for image",
        )

        assert image.metadata is not None
        assert "mock" in image.metadata
        assert image.metadata["mock"] is True

    @pytest.mark.asyncio
    async def test_free_images_have_photographer(self):
        """Test free images include photographer info."""
        service = ImageService(mock_mode=True)

        images = await service.get_free_images(
            query="test",
            count=1,
        )

        assert images[0].photographer is not None
        assert images[0].photographer_url is not None

    @pytest.mark.asyncio
    async def test_images_have_download_url(self):
        """Test images have download URLs."""
        service = ImageService(mock_mode=True)

        # Free images
        free_images = await service.get_free_images(
            query="test",
            count=1,
        )
        assert free_images[0].download_url is not None

        # AI images
        ai_image = await service.generate_ai_image(
            prompt="test",
        )
        assert ai_image.download_url is not None


class TestImageResult:
    """Tests for ImageResult dataclass."""

    def test_image_result_creation(self):
        """Test creating an image result."""
        result = ImageResult(
            url="https://example.com/image.jpg",
            source="pexels",
            width=1920,
            height=1080,
            alt_text="Test image",
            photographer="John Doe",
            photographer_url="https://pexels.com/@johndoe",
            download_url="https://example.com/download/image.jpg",
            cost_usd=Decimal("0"),
            metadata={"id": "123"},
        )

        assert result.url == "https://example.com/image.jpg"
        assert result.source == "pexels"
        assert result.width == 1920
        assert result.height == 1080
        assert result.photographer == "John Doe"
        assert result.cost_usd == Decimal("0")

    def test_image_result_defaults(self):
        """Test image result default values."""
        result = ImageResult(
            url="https://example.com/image.jpg",
            source="test",
            width=100,
            height=100,
            alt_text="Test",
        )

        assert result.photographer is None
        assert result.photographer_url is None
        assert result.download_url is None
        assert result.cost_usd == Decimal("0")
        assert result.metadata is None

    def test_ai_image_has_cost(self):
        """Test AI images have associated cost."""
        result = ImageResult(
            url="https://dalle.com/image.jpg",
            source="dalle",
            width=1024,
            height=1024,
            alt_text="AI generated image",
            cost_usd=Decimal("0.04"),
        )

        assert result.cost_usd == Decimal("0.04")
