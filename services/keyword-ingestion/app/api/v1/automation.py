"""Automation API endpoints for PHASE-004."""

import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user
from app.core.config import get_settings
from app.db.session import get_db
from app.models.keyword import Keyword
from app.models.keyword_list import KeywordList
from app.schemas.keyword import (
    CompetitorKeywordsRequest,
    CompetitorKeywordsResponse,
    EnrichKeywordsRequest,
    EnrichKeywordsResponse,
    PasteKeywordsRequest,
    PasteKeywordsResponse,
    TrendingKeywordsRequest,
    TrendingKeywordsResponse,
)
from app.services.event_publisher import event_publisher
from app.services.keyword_list_service import KeywordListService
from app.services.keyword_processor import KeywordProcessor

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/keyword-lists", tags=["Keyword Automation"])


@router.post("/enrich", response_model=EnrichKeywordsResponse)
async def enrich_keywords(
    request: EnrichKeywordsRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Enrich keywords in a list with data from Ahrefs or SEMrush.

    This endpoint triggers a background task to fetch keyword metrics
    (search volume, difficulty, CPC) and classify search intent.
    """
    service = KeywordListService(db)

    # Check if list exists
    keyword_list = await service.get_by_id(request.list_id)
    if not keyword_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Keyword list not found",
        )

    # Try to use Celery if available, otherwise use background task
    task_id = None
    try:
        from app.tasks import enrich_keywords_batch

        result = enrich_keywords_batch.delay(
            str(request.list_id), source=request.source
        )
        task_id = result.id
        logger.info(f"Started Celery enrichment task {task_id} for list {request.list_id}")
    except Exception as e:
        logger.warning(f"Celery not available, using background task: {e}")
        # Fall back to FastAPI background task
        background_tasks.add_task(
            _enrich_keywords_background,
            list_id=request.list_id,
            source=request.source,
            db_url=settings.DATABASE_URL,
        )

    return EnrichKeywordsResponse(
        list_id=request.list_id,
        status="processing",
        message=f"Keyword enrichment with {request.source} started",
        task_id=task_id,
    )


@router.post("/from-trends", response_model=TrendingKeywordsResponse)
async def create_from_trends(
    request: TrendingKeywordsRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch trending keywords from Google Trends.

    This creates a new keyword list with trending keywords from
    the specified geographic region.
    """
    task_id = None
    try:
        from app.tasks import discover_trending_keywords

        result = discover_trending_keywords.delay(
            str(request.workspace_id), geo=request.geo
        )
        task_id = result.id
        logger.info(f"Started Celery trends task {task_id} for workspace {request.workspace_id}")
    except Exception as e:
        logger.warning(f"Celery not available, using background task: {e}")
        background_tasks.add_task(
            _discover_trends_background,
            workspace_id=request.workspace_id,
            geo=request.geo,
            db_url=settings.DATABASE_URL,
        )

    return TrendingKeywordsResponse(
        workspace_id=request.workspace_id,
        status="processing",
        message=f"Trending keywords discovery for {request.geo} started",
        task_id=task_id,
    )


@router.post("/from-competitor", response_model=CompetitorKeywordsResponse)
async def create_from_competitor(
    request: CompetitorKeywordsRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pull keywords from a competitor domain.

    This creates a new keyword list with keywords that the
    competitor ranks for, fetched from Ahrefs.
    """
    task_id = None
    try:
        from app.tasks import pull_competitor_keywords

        result = pull_competitor_keywords.delay(
            str(request.workspace_id),
            competitor_domain=request.competitor_domain,
            limit=request.limit,
        )
        task_id = result.id
        logger.info(
            f"Started Celery competitor task {task_id} for {request.competitor_domain}"
        )
    except Exception as e:
        logger.warning(f"Celery not available, using background task: {e}")
        background_tasks.add_task(
            _pull_competitor_background,
            workspace_id=request.workspace_id,
            competitor_domain=request.competitor_domain,
            limit=request.limit,
            db_url=settings.DATABASE_URL,
        )

    return CompetitorKeywordsResponse(
        workspace_id=request.workspace_id,
        competitor_domain=request.competitor_domain,
        status="processing",
        message=f"Competitor keywords analysis for {request.competitor_domain} started",
        task_id=task_id,
    )


@router.post("/from-paste", response_model=PasteKeywordsResponse)
async def create_from_paste(
    request: PasteKeywordsRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a keyword list from pasted keywords.

    This allows users to directly paste a list of keywords
    without uploading a file.
    """
    processor = KeywordProcessor()

    # Process and deduplicate keywords
    processed = processor.process(request.keywords)

    if not processed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid keywords provided",
        )

    # Create keyword list
    keyword_list = KeywordList(
        workspace_id=request.workspace_id,
        name=request.name,
        description=request.description,
        source="paste",
        status="processing",
        created_by=current_user.id,
    )
    db.add(keyword_list)
    await db.flush()

    # Add keywords
    for text, normalized in processed:
        keyword = Keyword(
            list_id=keyword_list.id,
            text=text,
            normalized_text=normalized,
            status="pending",
            intent="unknown",
        )
        db.add(keyword)

    # Update list status
    keyword_list.total_keywords = len(processed)
    keyword_list.status = "completed"
    keyword_list.processed_at = datetime.now(timezone.utc)

    await db.commit()

    # Publish event
    try:
        await event_publisher.publish(
            "keyword.list.imported",
            {
                "list_id": keyword_list.id,
                "list_name": keyword_list.name,
                "total_keywords": len(processed),
                "source": "paste",
            },
            workspace_id=request.workspace_id,
        )
    except Exception as e:
        logger.warning(f"Failed to publish event: {e}")

    logger.info(
        f"Created keyword list {keyword_list.id} with {len(processed)} pasted keywords"
    )

    return PasteKeywordsResponse(
        list_id=keyword_list.id,
        name=keyword_list.name,
        total_keywords=len(processed),
        status="completed",
        message=f"Successfully imported {len(processed)} keywords",
    )


# Background task fallbacks when Celery is not available


async def _enrich_keywords_background(
    list_id: UUID,
    source: str,
    db_url: str,
):
    """Background task fallback for keyword enrichment."""
    from decimal import Decimal

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.connectors import AhrefsConnector, SEMrushConnector
    from app.ml import get_intent_classifier

    engine = create_async_engine(db_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    if source == "ahrefs":
        connector = AhrefsConnector()
    else:
        connector = SEMrushConnector()

    intent_classifier = get_intent_classifier(use_ml=False)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Keyword)
            .where(Keyword.list_id == list_id)
            .where(Keyword.status == "pending")
        )
        keywords = result.scalars().all()

        for kw in keywords:
            try:
                if source == "ahrefs":
                    metrics = await connector.get_keyword_metrics(kw.text)
                else:
                    metrics = await connector.get_keyword_overview(kw.text)

                intent_result = await intent_classifier.get_intent_with_confidence(kw.text)

                kw.search_volume = metrics.get("search_volume", 0)
                kw.keyword_difficulty = Decimal(str(metrics.get("keyword_difficulty", 0)))
                kw.intent = intent_result["intent"]
                kw.status = "processed"

            except Exception as e:
                logger.error(f"Error enriching keyword '{kw.text}': {e}")

        await db.commit()


async def _discover_trends_background(
    workspace_id: UUID,
    geo: str,
    db_url: str,
):
    """Background task fallback for trends discovery."""
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.connectors import GoogleTrendsConnector

    engine = create_async_engine(db_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    trends_connector = GoogleTrendsConnector()
    processor = KeywordProcessor()

    async with AsyncSessionLocal() as db:
        trends = await trends_connector.get_trending_searches(geo=geo)

        if not trends:
            return

        keyword_list = KeywordList(
            workspace_id=workspace_id,
            name=f"Trending Keywords {date.today()} ({geo})",
            source="google_trends",
            status="processing",
        )
        db.add(keyword_list)
        await db.flush()

        raw_keywords = [t["keyword"] for t in trends]
        processed = processor.process(raw_keywords)

        for text, normalized in processed:
            keyword = Keyword(
                list_id=keyword_list.id,
                text=text,
                normalized_text=normalized,
                status="pending",
                intent="unknown",
            )
            db.add(keyword)

        keyword_list.total_keywords = len(processed)
        keyword_list.status = "completed"
        keyword_list.processed_at = datetime.now(timezone.utc)

        await db.commit()


async def _pull_competitor_background(
    workspace_id: UUID,
    competitor_domain: str,
    limit: int,
    db_url: str,
):
    """Background task fallback for competitor keywords."""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.connectors import AhrefsConnector

    engine = create_async_engine(db_url)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    ahrefs = AhrefsConnector()
    processor = KeywordProcessor()

    async with AsyncSessionLocal() as db:
        keywords_data = await ahrefs.get_competitor_keywords(competitor_domain, limit=limit)

        if not keywords_data:
            return

        keyword_list = KeywordList(
            workspace_id=workspace_id,
            name=f"Competitor: {competitor_domain}",
            source="ahrefs_competitor",
            status="processing",
        )
        db.add(keyword_list)
        await db.flush()

        raw_keywords = [k["keyword"] for k in keywords_data]
        processed = processor.process(raw_keywords)

        for text, normalized in processed:
            keyword = Keyword(
                list_id=keyword_list.id,
                text=text,
                normalized_text=normalized,
                status="pending",
                intent="unknown",
            )
            db.add(keyword)

        keyword_list.total_keywords = len(processed)
        keyword_list.status = "completed"
        keyword_list.processed_at = datetime.now(timezone.utc)

        await db.commit()
