"""Analytics API endpoints."""

import logging
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query

from app.db.clickhouse import clickhouse_client
from app.schemas.performance import (
    ArticlePerformance,
    ArticlePerformanceResponse,
    PerformanceDataInput,
    PerformanceDataResponse,
    SummaryResponse,
    TopArticle,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/performance", response_model=PerformanceDataResponse)
async def record_performance(data: PerformanceDataInput):
    """
    Record manual performance data entry.

    This endpoint allows users to manually enter performance data
    from Google Analytics or Google Search Console.

    Body:
    - url: URL of the page/article
    - date: Date of the performance data (YYYY-MM-DD)
    - impressions: Number of impressions
    - clicks: Number of clicks
    - position: Average search position
    - workspace_id: (optional) Workspace ID
    - article_id: (optional) Article ID
    """
    try:
        # Prepare data for insertion
        insert_data = {
            "url": data.url,
            "date": data.date,
            "impressions": data.impressions,
            "clicks": data.clicks,
            "position": data.position,
            "workspace_id": data.workspace_id or "",
            "article_id": data.article_id or "",
            "ai_model_used": data.ai_model_used or "",
            "prompt_id": data.prompt_id or "",
            "cost_usd": data.cost_usd or 0.0,
        }

        # Insert into ClickHouse
        await clickhouse_client.insert_performance(insert_data)

        url_hash = clickhouse_client.url_hash(data.url)

        logger.info(f"Recorded performance data for URL: {data.url}")

        return PerformanceDataResponse(
            success=True,
            message="Performance data recorded successfully",
            url_hash=url_hash,
        )
    except Exception as e:
        logger.error(f"Failed to record performance data: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to record performance data: {str(e)}"
        )


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    workspace_id: str = Query(..., description="Workspace ID"),
    date_from: str = Query(
        None, description="Start date (YYYY-MM-DD). Defaults to 30 days ago."
    ),
    date_to: str = Query(
        None, description="End date (YYYY-MM-DD). Defaults to today."
    ),
):
    """
    Get performance summary for a workspace.

    Returns aggregated metrics including:
    - Total impressions
    - Total clicks
    - Average position
    - Number of articles ranking
    - Top performing articles
    """
    try:
        # Set default date range (last 30 days)
        if not date_to:
            date_to = str(date.today())
        if not date_from:
            date_from = str(date.today() - timedelta(days=30))

        # Get summary from ClickHouse
        summary = await clickhouse_client.get_summary(workspace_id, date_from, date_to)

        return SummaryResponse(
            workspace_id=workspace_id,
            date_from=date_from,
            date_to=date_to,
            total_impressions=summary["total_impressions"],
            total_clicks=summary["total_clicks"],
            avg_position=summary["avg_position"],
            articles_ranking=summary["articles_ranking"],
            top_articles=[TopArticle(**a) for a in summary.get("top_articles", [])],
        )
    except Exception as e:
        logger.error(f"Failed to get summary: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get summary: {str(e)}"
        )


@router.get("/articles/{article_id}/performance", response_model=ArticlePerformanceResponse)
async def get_article_performance(
    article_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to fetch"),
):
    """
    Get time series performance data for a specific article.

    Returns daily performance metrics including:
    - Date
    - Impressions
    - Clicks
    - Position
    """
    try:
        # Get article performance from ClickHouse
        data = await clickhouse_client.get_article_performance(article_id, days)

        return ArticlePerformanceResponse(
            article_id=article_id,
            data=[ArticlePerformance(**d) for d in data],
        )
    except Exception as e:
        logger.error(f"Failed to get article performance: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get article performance: {str(e)}"
        )
