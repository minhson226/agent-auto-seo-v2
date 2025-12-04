"""Image API endpoints for free stock and AI-generated images."""

import logging
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, get_current_user
from app.services.image_generator import ImageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/images", tags=["Images"])


class ImageSearchRequest(BaseModel):
    """Request for image search."""

    query: str = Field(..., min_length=1, max_length=500)
    count: int = Field(default=5, ge=1, le=20)
    orientation: str = Field(default="landscape")


class ImageGenerateRequest(BaseModel):
    """Request for AI image generation."""

    prompt: str = Field(..., min_length=1, max_length=4000)
    size: str = Field(default="1024x1024")
    quality: str = Field(default="standard")


class ImageResponse(BaseModel):
    """Response for a single image."""

    url: str
    source: str
    width: int
    height: int
    alt_text: str
    photographer: Optional[str] = None
    photographer_url: Optional[str] = None
    download_url: Optional[str] = None
    cost_usd: str


class ImageSearchResponse(BaseModel):
    """Response for image search."""

    images: List[ImageResponse]
    query: str
    total: int


@router.post("/search", response_model=ImageSearchResponse)
async def search_free_images(
    request: ImageSearchRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Search for free stock images from Pexels and Unsplash.

    Returns high-quality images that can be used for free with attribution.
    """
    image_service = ImageService()

    try:
        results = await image_service.get_free_images(
            query=request.query,
            count=request.count,
            orientation=request.orientation,
        )

        images = [
            ImageResponse(
                url=img.url,
                source=img.source,
                width=img.width,
                height=img.height,
                alt_text=img.alt_text,
                photographer=img.photographer,
                photographer_url=img.photographer_url,
                download_url=img.download_url,
                cost_usd=str(img.cost_usd),
            )
            for img in results
        ]

        return ImageSearchResponse(
            images=images,
            query=request.query,
            total=len(images),
        )

    except Exception as e:
        logger.error(f"Image search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image search failed",
        )


@router.post("/generate", response_model=ImageResponse)
async def generate_ai_image(
    request: ImageGenerateRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Generate an AI image using DALL-E 3.

    Creates a unique image based on the provided prompt.
    Pricing:
    - Standard quality: $0.04 for 1024x1024, $0.08 for larger sizes
    - HD quality: $0.08 for 1024x1024, $0.12 for larger sizes
    """
    # Validate size
    valid_sizes = ["1024x1024", "1024x1792", "1792x1024"]
    if request.size not in valid_sizes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid size. Valid sizes: {', '.join(valid_sizes)}",
        )

    # Validate quality
    valid_qualities = ["standard", "hd"]
    if request.quality not in valid_qualities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid quality. Valid qualities: {', '.join(valid_qualities)}",
        )

    image_service = ImageService()

    try:
        result = await image_service.generate_ai_image(
            prompt=request.prompt,
            size=request.size,
            quality=request.quality,
        )

        if not result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI image generation failed",
            )

        return ImageResponse(
            url=result.url,
            source=result.source,
            width=result.width,
            height=result.height,
            alt_text=result.alt_text,
            photographer=result.photographer,
            photographer_url=result.photographer_url,
            download_url=result.download_url,
            cost_usd=str(result.cost_usd),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI image generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI image generation failed",
        )
