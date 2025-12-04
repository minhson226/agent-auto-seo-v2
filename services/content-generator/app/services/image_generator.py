"""Image service for free stock images and AI image generation."""

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class ImageResult:
    """Result from image search or generation."""

    url: str
    source: str  # 'pexels', 'unsplash', 'dalle', 'stable-diffusion'
    width: int
    height: int
    alt_text: str
    photographer: Optional[str] = None
    photographer_url: Optional[str] = None
    download_url: Optional[str] = None
    cost_usd: Decimal = Decimal("0")
    metadata: Optional[Dict[str, Any]] = None


class ImageService:
    """Service for fetching free stock images and generating AI images.

    Supports:
    - Pexels API for free stock photos
    - Unsplash API for free stock photos
    - DALL-E 3 for AI image generation
    - Stable Diffusion for AI image generation (via API)
    """

    def __init__(self, mock_mode: bool = False):
        """Initialize the image service.

        Args:
            mock_mode: If True, returns mock images for testing
        """
        self._mock_mode = mock_mode
        self.pexels_api_key = getattr(settings, "PEXELS_API_KEY", "")
        self.unsplash_access_key = getattr(settings, "UNSPLASH_ACCESS_KEY", "")
        self.openai_api_key = settings.OPENAI_API_KEY

        # Initialize OpenAI client for DALL-E
        self._openai_client = None
        if self.openai_api_key and not mock_mode:
            try:
                from openai import AsyncOpenAI

                self._openai_client = AsyncOpenAI(api_key=self.openai_api_key)
            except ImportError:
                logger.warning("OpenAI package not installed for image generation")

    @property
    def mock_mode(self) -> bool:
        """Check if service is in mock mode."""
        return self._mock_mode

    async def get_free_images(
        self,
        query: str,
        count: int = 5,
        orientation: str = "landscape",
    ) -> List[ImageResult]:
        """Get free stock images from Pexels and Unsplash.

        Args:
            query: Search query for images
            count: Number of images to return (max per source)
            orientation: Image orientation ('landscape', 'portrait', 'square')

        Returns:
            List of image results
        """
        if self._mock_mode:
            return self._get_mock_images(query, count)

        results = []

        # Try Pexels
        if self.pexels_api_key:
            try:
                pexels_results = await self._search_pexels(query, count, orientation)
                results.extend(pexels_results)
            except Exception as e:
                logger.warning(f"Pexels search failed: {e}")

        # Try Unsplash
        if self.unsplash_access_key:
            try:
                unsplash_results = await self._search_unsplash(query, count, orientation)
                results.extend(unsplash_results)
            except Exception as e:
                logger.warning(f"Unsplash search failed: {e}")

        # If no API keys configured, return mock results
        if not results:
            logger.warning("No image API keys configured, returning mock images")
            results = self._get_mock_images(query, count)

        return results[:count]

    async def _search_pexels(
        self,
        query: str,
        count: int,
        orientation: str,
    ) -> List[ImageResult]:
        """Search Pexels for images.

        Args:
            query: Search query
            count: Number of images
            orientation: Image orientation

        Returns:
            List of Pexels image results
        """
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": self.pexels_api_key}
        params = {
            "query": query,
            "per_page": count,
            "orientation": orientation,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        results = []
        for photo in data.get("photos", []):
            results.append(
                ImageResult(
                    url=photo["src"]["large"],
                    source="pexels",
                    width=photo["width"],
                    height=photo["height"],
                    alt_text=photo.get("alt", query),
                    photographer=photo.get("photographer"),
                    photographer_url=photo.get("photographer_url"),
                    download_url=photo["src"]["original"],
                    cost_usd=Decimal("0"),
                    metadata={"pexels_id": photo["id"]},
                )
            )

        return results

    async def _search_unsplash(
        self,
        query: str,
        count: int,
        orientation: str,
    ) -> List[ImageResult]:
        """Search Unsplash for images.

        Args:
            query: Search query
            count: Number of images
            orientation: Image orientation

        Returns:
            List of Unsplash image results
        """
        url = "https://api.unsplash.com/search/photos"
        headers = {"Authorization": f"Client-ID {self.unsplash_access_key}"}
        params = {
            "query": query,
            "per_page": count,
            "orientation": orientation,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

        results = []
        for photo in data.get("results", []):
            results.append(
                ImageResult(
                    url=photo["urls"]["regular"],
                    source="unsplash",
                    width=photo["width"],
                    height=photo["height"],
                    alt_text=photo.get("alt_description") or query,
                    photographer=photo["user"]["name"],
                    photographer_url=photo["user"]["links"]["html"],
                    download_url=photo["urls"]["full"],
                    cost_usd=Decimal("0"),
                    metadata={"unsplash_id": photo["id"]},
                )
            )

        return results

    async def generate_ai_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        model: str = "dall-e-3",
        quality: str = "standard",
    ) -> Optional[ImageResult]:
        """Generate an AI image using DALL-E 3.

        Args:
            prompt: The image generation prompt
            size: Image size ('1024x1024', '1024x1792', '1792x1024')
            model: Model to use ('dall-e-3')
            quality: Quality level ('standard', 'hd')

        Returns:
            Generated image result or None if failed
        """
        if self._mock_mode or not self._openai_client:
            return self._generate_mock_ai_image(prompt, size)

        try:
            response = await self._openai_client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality=quality,
                n=1,
            )

            image_data = response.data[0]
            width, height = map(int, size.split("x"))

            # DALL-E 3 pricing (as of late 2024)
            cost = Decimal("0.04") if quality == "standard" else Decimal("0.08")
            if size == "1024x1792" or size == "1792x1024":
                cost = Decimal("0.08") if quality == "standard" else Decimal("0.12")

            return ImageResult(
                url=image_data.url,
                source="dalle",
                width=width,
                height=height,
                alt_text=prompt[:100],
                download_url=image_data.url,
                cost_usd=cost,
                metadata={
                    "model": model,
                    "quality": quality,
                    "revised_prompt": getattr(image_data, "revised_prompt", None),
                },
            )

        except Exception as e:
            logger.error(f"DALL-E image generation failed: {e}")
            return None

    def _get_mock_images(self, query: str, count: int) -> List[ImageResult]:
        """Generate mock image results for testing.

        Args:
            query: Search query
            count: Number of mock images

        Returns:
            List of mock image results
        """
        results = []
        for i in range(count):
            results.append(
                ImageResult(
                    url=f"https://mock.pexels.com/photos/{i + 1}?query={quote_plus(query)}",
                    source="pexels-mock",
                    width=1920,
                    height=1080,
                    alt_text=f"Mock image for {query}",
                    photographer="Mock Photographer",
                    photographer_url="https://mock.pexels.com/@photographer",
                    download_url=f"https://mock.pexels.com/download/{i + 1}",
                    cost_usd=Decimal("0"),
                    metadata={"mock": True, "index": i},
                )
            )
        return results

    def _generate_mock_ai_image(self, prompt: str, size: str) -> ImageResult:
        """Generate a mock AI image for testing.

        Args:
            prompt: The image prompt
            size: Image size

        Returns:
            Mock AI image result
        """
        width, height = map(int, size.split("x"))
        return ImageResult(
            url=f"https://mock.dalle.com/generate?prompt={quote_plus(prompt[:50])}",
            source="dalle-mock",
            width=width,
            height=height,
            alt_text=prompt[:100],
            download_url=f"https://mock.dalle.com/download?prompt={quote_plus(prompt[:50])}",
            cost_usd=Decimal("0.04"),
            metadata={"mock": True, "prompt": prompt},
        )


# Global image service instance
image_service = ImageService()
