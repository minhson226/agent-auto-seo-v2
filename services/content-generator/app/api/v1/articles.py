"""Articles API endpoints."""

import json
import logging
import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.article import (
    ArticleCreate,
    ArticleGenerateRequest,
    ArticleImageResponse,
    ArticleListResponse,
    ArticleResponse,
    ArticleUpdate,
    PaginatedArticleResponse,
)
from app.services.article_service import ArticleService
from app.services.content_generator import content_generator
from app.services.event_publisher import event_publisher
from app.services.image_storage import image_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/articles", tags=["Articles"])

# Allowed image content types
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/generate", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def generate_article(
    request: ArticleGenerateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate an article from a content plan using GPT-3.5.

    This endpoint takes a content plan ID, retrieves the plan details,
    and uses OpenAI GPT-3.5 to generate SEO-optimized content.
    """
    # Determine schema based on database type
    db_url = os.environ.get("DATABASE_URL", "")
    is_sqlite = "sqlite" in db_url

    # Query content plan - handle different databases
    if is_sqlite:
        # SQLite test database - content_plans table should exist without schema
        query = text("""
            SELECT id, workspace_id, title, target_keywords, estimated_word_count
            FROM content_plans
            WHERE id = :plan_id
        """)
    else:
        # PostgreSQL with schema
        query = text("""
            SELECT id, workspace_id, title, target_keywords, estimated_word_count
            FROM autoseo.content_plans
            WHERE id = :plan_id
        """)

    try:
        result = await db.execute(query, {"plan_id": str(request.plan_id)})
        plan_row = result.fetchone()
    except Exception as e:
        # Handle case where content_plans table doesn't exist (test environment)
        logger.warning(f"Could not query content_plans: {e}")
        plan_row = None

    if not plan_row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content plan not found",
        )

    plan_id, workspace_id, title, target_keywords, estimated_word_count = plan_row

    # Parse target_keywords - it could be JSON or array
    if isinstance(target_keywords, str):
        try:
            keywords = json.loads(target_keywords)
        except (json.JSONDecodeError, TypeError):
            keywords = []
    elif isinstance(target_keywords, list):
        keywords = target_keywords
    else:
        keywords = []

    try:
        # Generate content using OpenAI
        generation_result = await content_generator.generate_article(
            title=title,
            target_keywords=keywords,
            estimated_word_count=estimated_word_count,
        )

        # Save article to database
        article_service = ArticleService(db)
        article = await article_service.create_from_generation(
            workspace_id=UUID(str(workspace_id)),
            plan_id=UUID(str(plan_id)),
            title=title,
            content=generation_result.content,
            model=generation_result.model,
            cost_usd=generation_result.cost_usd,
            word_count=generation_result.word_count,
            metadata={
                "tokens_used": generation_result.tokens_used,
                "generated_from_plan": str(plan_id),
            },
        )

        # Publish event
        try:
            await event_publisher.publish(
                "article.generated",
                {
                    "article_id": article.id,
                    "title": article.title,
                    "word_count": article.word_count,
                    "cost": article.cost_usd,
                    "model": article.ai_model_used,
                    "plan_id": str(plan_id),
                },
                workspace_id=article.workspace_id,
            )
        except Exception as e:
            logger.warning(f"Failed to publish event: {e}")

        return ArticleResponse(
            id=article.id,
            workspace_id=article.workspace_id,
            plan_id=article.plan_id,
            title=article.title,
            content=article.content,
            status=article.status,
            ai_model_used=article.ai_model_used,
            cost_usd=article.cost_usd,
            word_count=article.word_count,
            metadata=article.generation_metadata,
            images=[],
            created_at=article.created_at,
            updated_at=article.updated_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Content generation failed",
        )


@router.post("", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    data: ArticleCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new article directly (without AI generation)."""
    service = ArticleService(db)
    article = await service.create(data)

    return ArticleResponse(
        id=article.id,
        workspace_id=article.workspace_id,
        plan_id=article.plan_id,
        title=article.title,
        content=article.content,
        status=article.status,
        ai_model_used=article.ai_model_used,
        cost_usd=article.cost_usd,
        word_count=article.word_count,
        metadata=article.generation_metadata,
        images=[],
        created_at=article.created_at,
        updated_at=article.updated_at,
    )


@router.get("", response_model=PaginatedArticleResponse)
async def list_articles(
    workspace_id: UUID,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List articles for a workspace.

    Optionally filter by status (draft, published, archived).
    """
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 1
    if page_size > 100:
        page_size = 100

    service = ArticleService(db)
    articles, total = await service.get_by_workspace(
        workspace_id=workspace_id,
        status=status,
        page=page,
        page_size=page_size,
    )

    data = []
    for article in articles:
        data.append(
            ArticleListResponse(
                id=article.id,
                workspace_id=article.workspace_id,
                plan_id=article.plan_id,
                title=article.title,
                status=article.status,
                ai_model_used=article.ai_model_used,
                cost_usd=article.cost_usd,
                word_count=article.word_count,
                image_count=len(article.images) if article.images else 0,
                created_at=article.created_at,
                updated_at=article.updated_at,
            )
        )

    return PaginatedArticleResponse(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific article."""
    service = ArticleService(db)
    article = await service.get_by_id(article_id)

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    images = [
        ArticleImageResponse(
            id=img.id,
            article_id=img.article_id,
            filename=img.filename,
            original_filename=img.original_filename,
            content_type=img.content_type,
            size_bytes=img.size_bytes,
            storage_path=img.storage_path,
            created_at=img.created_at,
        )
        for img in (article.images or [])
    ]

    return ArticleResponse(
        id=article.id,
        workspace_id=article.workspace_id,
        plan_id=article.plan_id,
        title=article.title,
        content=article.content,
        status=article.status,
        ai_model_used=article.ai_model_used,
        cost_usd=article.cost_usd,
        word_count=article.word_count,
        metadata=article.generation_metadata,
        images=images,
        created_at=article.created_at,
        updated_at=article.updated_at,
    )


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: UUID,
    data: ArticleUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an article."""
    service = ArticleService(db)
    article = await service.update(article_id, data)

    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    images = [
        ArticleImageResponse(
            id=img.id,
            article_id=img.article_id,
            filename=img.filename,
            original_filename=img.original_filename,
            content_type=img.content_type,
            size_bytes=img.size_bytes,
            storage_path=img.storage_path,
            created_at=img.created_at,
        )
        for img in (article.images or [])
    ]

    return ArticleResponse(
        id=article.id,
        workspace_id=article.workspace_id,
        plan_id=article.plan_id,
        title=article.title,
        content=article.content,
        status=article.status,
        ai_model_used=article.ai_model_used,
        cost_usd=article.cost_usd,
        word_count=article.word_count,
        metadata=article.generation_metadata,
        images=images,
        created_at=article.created_at,
        updated_at=article.updated_at,
    )


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an article."""
    service = ArticleService(db)

    # Get article first to delete images from storage
    article = await service.get_by_id(article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    # Delete images from storage
    for img in (article.images or []):
        try:
            await image_storage.delete_image(img.storage_path)
        except Exception as e:
            logger.warning(f"Failed to delete image from storage: {e}")

    # Delete article from database (cascade will delete image records)
    deleted = await service.delete(article_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )


@router.post("/{article_id}/images", response_model=ArticleImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    article_id: UUID,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload an image for an article.

    Accepts JPEG, PNG, GIF, and WebP images up to 10MB.
    """
    service = ArticleService(db)

    # Check article exists
    article = await service.get_by_id(article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    # Validate content type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}",
        )

    # Read file content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image too large. Maximum size: {MAX_IMAGE_SIZE // (1024 * 1024)}MB",
        )

    try:
        # Upload to storage
        storage_path = await image_storage.upload_image(
            article_id=article_id,
            file_content=content,
            original_filename=file.filename or "image.jpg",
            content_type=file.content_type or "image/jpeg",
        )

        # Extract filename from storage path
        filename = storage_path.split("/")[-1]

        # Save image record to database
        image = await service.add_image(
            article_id=article_id,
            filename=filename,
            original_filename=file.filename or "image.jpg",
            content_type=file.content_type or "image/jpeg",
            size_bytes=len(content),
            storage_path=storage_path,
        )

        if not image:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save image record",
            )

        return ArticleImageResponse(
            id=image.id,
            article_id=image.article_id,
            filename=image.filename,
            original_filename=image.original_filename,
            content_type=image.content_type,
            size_bytes=image.size_bytes,
            storage_path=image.storage_path,
            created_at=image.created_at,
        )

    except Exception as e:
        logger.error(f"Image upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image upload failed",
        )


@router.delete("/{article_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    article_id: UUID,
    image_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an image from an article."""
    service = ArticleService(db)

    # Get article to verify it exists
    article = await service.get_by_id(article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    # Find the image
    image = None
    for img in (article.images or []):
        if img.id == image_id:
            image = img
            break

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    # Delete from storage
    try:
        await image_storage.delete_image(image.storage_path)
    except Exception as e:
        logger.warning(f"Failed to delete image from storage: {e}")

    # Delete from database
    deleted = await service.delete_image(image_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )
