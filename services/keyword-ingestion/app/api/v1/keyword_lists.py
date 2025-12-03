"""Keyword lists API endpoints."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.keyword import (
    KeywordListCreate,
    KeywordListResponse,
    KeywordListStats,
    PaginatedKeywordListResponse,
)
from app.services.event_publisher import event_publisher
from app.services.file_parser import FileParser
from app.services.keyword_list_service import KeywordListService
from app.services.keyword_processor import KeywordProcessor
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/keyword-lists", tags=["Keyword Lists"])


async def process_keywords_background(
    list_id: UUID,
    workspace_id: UUID,
    content: bytes,
    filename: str,
    db_url: str,
):
    """Background task to process keywords from uploaded file."""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    # Create a new database session for the background task
    engine = create_async_engine(db_url)
    AsyncSessionLocal = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with AsyncSessionLocal() as db:
        service = KeywordListService(db)
        file_parser = FileParser()
        processor = KeywordProcessor()

        try:
            # Parse the file
            raw_keywords = await file_parser.parse_file(content, filename)

            if not raw_keywords:
                await service.update_status(
                    list_id,
                    status="failed",
                    error_message="No keywords found in file",
                )
                return

            # Process keywords (normalize and deduplicate)
            processed_keywords = processor.process(raw_keywords)

            # Add keywords to database
            count = await service.add_keywords(list_id, processed_keywords)

            # Update list status
            await service.update_status(
                list_id,
                status="completed",
                total_keywords=count,
            )

            # Publish event
            try:
                keyword_list = await service.get_by_id(list_id)
                if keyword_list:
                    await event_publisher.publish(
                        "keyword.list.imported",
                        {
                            "list_id": list_id,
                            "list_name": keyword_list.name,
                            "total_keywords": count,
                            "source": keyword_list.source,
                        },
                        workspace_id=workspace_id,
                    )
            except Exception as e:
                logger.warning(f"Failed to publish event: {e}")

            logger.info(f"Processed {count} keywords for list {list_id}")

        except ValueError as e:
            await service.update_status(
                list_id,
                status="failed",
                error_message=str(e),
            )
            logger.error(f"Failed to process keywords: {e}")
        except Exception as e:
            await service.update_status(
                list_id,
                status="failed",
                error_message=f"Unexpected error: {str(e)}",
            )
            logger.exception(f"Unexpected error processing keywords: {e}")


@router.post("", response_model=KeywordListResponse, status_code=status.HTTP_201_CREATED)
async def create_keyword_list(
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    workspace_id: UUID = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a CSV or TXT file to create a keyword list.

    The file will be processed in the background. Check the status
    of the keyword list to see when processing is complete.
    """
    # Validate file type
    filename = file.filename or "unknown"
    if not filename.lower().endswith((".csv", ".txt")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Expected .csv or .txt file",
        )

    # Read file content
    content = await file.read()

    # Validate file size
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB",
        )

    # Determine source based on file type
    source = "csv_upload" if filename.lower().endswith(".csv") else "txt_upload"

    # Upload file to storage
    storage = StorageService()
    try:
        file_url = await storage.upload_file(
            content=content,
            filename=filename,
            workspace_id=str(workspace_id),
            content_type=file.content_type or "application/octet-stream",
        )
    except Exception as e:
        logger.warning(f"Failed to upload file to storage: {e}")
        file_url = None

    # Create keyword list record
    service = KeywordListService(db)
    create_data = KeywordListCreate(
        name=name,
        description=description,
        workspace_id=workspace_id,
    )
    keyword_list = await service.create(
        data=create_data,
        user_id=current_user.id,
        source=source,
        source_file_url=file_url,
    )

    # Schedule background processing
    background_tasks.add_task(
        process_keywords_background,
        list_id=keyword_list.id,
        workspace_id=workspace_id,
        content=content,
        filename=filename,
        db_url=settings.DATABASE_URL,
    )

    return KeywordListResponse.model_validate(keyword_list)


@router.get("", response_model=PaginatedKeywordListResponse)
async def list_keyword_lists(
    workspace_id: UUID,
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List keyword lists for a workspace."""
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 1
    if page_size > 100:
        page_size = 100

    service = KeywordListService(db)
    keyword_lists, total = await service.get_by_workspace(
        workspace_id=workspace_id,
        status=status_filter,
        page=page,
        page_size=page_size,
    )

    return PaginatedKeywordListResponse(
        data=[KeywordListResponse.model_validate(kl) for kl in keyword_lists],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{list_id}", response_model=KeywordListResponse)
async def get_keyword_list(
    list_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific keyword list."""
    service = KeywordListService(db)
    keyword_list = await service.get_by_id(list_id)

    if not keyword_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword list not found",
        )

    return KeywordListResponse.model_validate(keyword_list)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_keyword_list(
    list_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a keyword list and all its keywords."""
    service = KeywordListService(db)
    deleted = await service.delete(list_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword list not found",
        )


@router.get("/{list_id}/stats", response_model=KeywordListStats)
async def get_keyword_list_stats(
    list_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get statistics for a keyword list."""
    service = KeywordListService(db)

    # Check if list exists
    keyword_list = await service.get_by_id(list_id)
    if not keyword_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword list not found",
        )

    return await service.get_stats(list_id)
