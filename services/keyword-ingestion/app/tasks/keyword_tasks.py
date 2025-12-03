"""Celery tasks for keyword automation."""

import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def enrich_keywords_batch(
    self,
    list_id: str,
    source: str = "ahrefs",
    db_url: Optional[str] = None,
):
    """Enrich keywords with data from Ahrefs/SEMrush.

    Args:
        list_id: UUID of the keyword list to enrich
        source: Data source ('ahrefs' or 'semrush')
        db_url: Database URL for connection
    """
    import asyncio
    from decimal import Decimal

    from sqlalchemy import select, update
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.connectors import AhrefsConnector, SEMrushConnector
    from app.core.config import get_settings
    from app.ml import get_intent_classifier
    from app.models.keyword import Keyword
    from app.services.event_publisher import EventPublisher

    async def _enrich():
        settings = get_settings()
        engine = create_async_engine(db_url or settings.DATABASE_URL)
        AsyncSessionLocal = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        # Initialize connectors
        if source == "ahrefs":
            connector = AhrefsConnector()
        else:
            connector = SEMrushConnector()

        intent_classifier = get_intent_classifier(use_ml=False)  # Use pattern-based for speed

        async with AsyncSessionLocal() as db:
            # Get all pending keywords from the list
            result = await db.execute(
                select(Keyword)
                .where(Keyword.list_id == UUID(list_id))
                .where(Keyword.status == "pending")
            )
            keywords = result.scalars().all()

            logger.info(f"Enriching {len(keywords)} keywords for list {list_id}")

            enriched_count = 0
            for kw in keywords:
                try:
                    # Get metrics from connector
                    if source == "ahrefs":
                        metrics = await connector.get_keyword_metrics(kw.text)
                    else:
                        metrics = await connector.get_keyword_overview(kw.text)

                    # Classify intent
                    intent_result = await intent_classifier.get_intent_with_confidence(kw.text)

                    # Update keyword
                    kw.search_volume = metrics.get("search_volume", 0)
                    kw.keyword_difficulty = Decimal(str(metrics.get("keyword_difficulty", 0)))
                    kw.intent = intent_result["intent"]
                    kw.status = "processed"
                    kw.metadata_["enrichment"] = {
                        "source": source,
                        "cpc": metrics.get("cpc", 0),
                        "clicks": metrics.get("clicks", 0),
                        "intent_confidence": intent_result["confidence"],
                        "enriched_at": datetime.now(timezone.utc).isoformat(),
                    }

                    enriched_count += 1

                except Exception as e:
                    logger.error(f"Error enriching keyword '{kw.text}': {e}")
                    kw.metadata_["enrichment_error"] = str(e)

            await db.commit()

            # Publish event
            try:
                publisher = EventPublisher()
                await publisher.connect()
                await publisher.publish(
                    "keyword.list.enriched",
                    {
                        "list_id": list_id,
                        "source": source,
                        "total_enriched": enriched_count,
                    },
                )
                await publisher.disconnect()
            except Exception as e:
                logger.warning(f"Failed to publish enrichment event: {e}")

            logger.info(f"Enriched {enriched_count} keywords for list {list_id}")
            return {"list_id": list_id, "enriched": enriched_count}

    return asyncio.get_event_loop().run_until_complete(_enrich())


@celery_app.task(bind=True, max_retries=3)
def discover_trending_keywords(
    self,
    workspace_id: str,
    geo: str = "US",
    db_url: Optional[str] = None,
):
    """Discover trending keywords from Google Trends.

    Args:
        workspace_id: UUID of the workspace
        geo: Geographic region code
        db_url: Database URL for connection
    """
    import asyncio
    from datetime import date

    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.connectors import GoogleTrendsConnector
    from app.core.config import get_settings
    from app.models.keyword import Keyword
    from app.models.keyword_list import KeywordList
    from app.services.keyword_processor import KeywordProcessor

    async def _discover():
        settings = get_settings()
        engine = create_async_engine(db_url or settings.DATABASE_URL)
        AsyncSessionLocal = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        trends_connector = GoogleTrendsConnector()
        processor = KeywordProcessor()

        async with AsyncSessionLocal() as db:
            # Get trending searches
            trends = await trends_connector.get_trending_searches(geo=geo)

            if not trends:
                logger.warning(f"No trending searches found for geo={geo}")
                return {"workspace_id": workspace_id, "keywords_added": 0}

            # Create new keyword list
            keyword_list = KeywordList(
                workspace_id=UUID(workspace_id),
                name=f"Trending Keywords {date.today()} ({geo})",
                description=f"Automatically discovered trending keywords from Google Trends ({geo})",
                source="google_trends",
                status="processing",
            )
            db.add(keyword_list)
            await db.flush()

            # Process and add keywords
            raw_keywords = [t["keyword"] for t in trends]
            processed = processor.process(raw_keywords)

            for text, normalized in processed:
                keyword = Keyword(
                    list_id=keyword_list.id,
                    text=text,
                    normalized_text=normalized,
                    status="pending",
                    intent="unknown",
                    metadata_={"source": "google_trends", "geo": geo},
                )
                db.add(keyword)

            keyword_list.total_keywords = len(processed)
            keyword_list.status = "completed"
            keyword_list.processed_at = datetime.now(timezone.utc)

            await db.commit()

            # Trigger enrichment
            enrich_keywords_batch.delay(str(keyword_list.id), source="ahrefs")

            logger.info(
                f"Created trending keywords list {keyword_list.id} with {len(processed)} keywords"
            )
            return {
                "workspace_id": workspace_id,
                "list_id": str(keyword_list.id),
                "keywords_added": len(processed),
            }

    return asyncio.get_event_loop().run_until_complete(_discover())


@celery_app.task(bind=True, max_retries=3)
def pull_competitor_keywords(
    self,
    workspace_id: str,
    competitor_domain: str,
    limit: int = 100,
    db_url: Optional[str] = None,
):
    """Pull keywords from a competitor domain.

    Args:
        workspace_id: UUID of the workspace
        competitor_domain: Competitor domain to analyze
        limit: Maximum number of keywords to pull
        db_url: Database URL for connection
    """
    import asyncio

    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.connectors import AhrefsConnector
    from app.core.config import get_settings
    from app.models.keyword import Keyword
    from app.models.keyword_list import KeywordList
    from app.services.keyword_processor import KeywordProcessor

    async def _pull():
        settings = get_settings()
        engine = create_async_engine(db_url or settings.DATABASE_URL)
        AsyncSessionLocal = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

        ahrefs = AhrefsConnector()
        processor = KeywordProcessor()

        async with AsyncSessionLocal() as db:
            # Get competitor keywords
            keywords_data = await ahrefs.get_competitor_keywords(
                competitor_domain, limit=limit
            )

            if not keywords_data:
                logger.warning(f"No keywords found for competitor {competitor_domain}")
                return {"workspace_id": workspace_id, "keywords_added": 0}

            # Create new keyword list
            keyword_list = KeywordList(
                workspace_id=UUID(workspace_id),
                name=f"Competitor: {competitor_domain}",
                description=f"Keywords from competitor analysis of {competitor_domain}",
                source="ahrefs_competitor",
                status="processing",
            )
            db.add(keyword_list)
            await db.flush()

            # Process and add keywords
            raw_keywords = [k["keyword"] for k in keywords_data]
            processed = processor.process(raw_keywords)

            for i, (text, normalized) in enumerate(processed):
                original_data = keywords_data[i] if i < len(keywords_data) else {}
                keyword = Keyword(
                    list_id=keyword_list.id,
                    text=text,
                    normalized_text=normalized,
                    status="pending",
                    intent="unknown",
                    search_volume=original_data.get("search_volume", 0),
                    metadata_={
                        "source": "ahrefs_competitor",
                        "competitor": competitor_domain,
                        "position": original_data.get("position", 0),
                        "traffic": original_data.get("traffic", 0),
                        "url": original_data.get("url", ""),
                    },
                )
                db.add(keyword)

            keyword_list.total_keywords = len(processed)
            keyword_list.status = "completed"
            keyword_list.processed_at = datetime.now(timezone.utc)

            await db.commit()

            logger.info(
                f"Created competitor keywords list {keyword_list.id} with {len(processed)} keywords"
            )
            return {
                "workspace_id": workspace_id,
                "list_id": str(keyword_list.id),
                "keywords_added": len(processed),
                "competitor": competitor_domain,
            }

    return asyncio.get_event_loop().run_until_complete(_pull())


@celery_app.task
def discover_trending_keywords_scheduled():
    """Scheduled task to discover trending keywords for all active workspaces."""
    logger.info("Running scheduled trending keywords discovery")
    # This would need workspace management - for now just log
    # In production, query active workspaces and call discover_trending_keywords for each
    return {"status": "scheduled_run_completed"}


@celery_app.task
def refresh_keyword_enrichment_scheduled():
    """Scheduled task to refresh keyword enrichment for stale data."""
    logger.info("Running scheduled keyword enrichment refresh")
    # This would query keywords with old enrichment data and re-enrich
    # For now just log
    return {"status": "scheduled_run_completed"}
