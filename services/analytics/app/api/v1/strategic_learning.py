"""Strategic Learning API endpoints for data sync and analysis."""

import logging
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.analyzer import performance_analyzer
from app.alerting import alerting_engine, Alert
from app.tasks.sync_tasks import sync_analytics_daily, sync_single_site

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response Models
class SyncRequest(BaseModel):
    """Request to trigger analytics sync."""

    workspace_id: Optional[str] = None
    site_url: Optional[str] = None
    ga_property_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class SyncResponse(BaseModel):
    """Response from analytics sync."""

    success: bool
    message: str
    workspaces_processed: int = 0
    sites_synced: int = 0
    records_inserted: int = 0
    errors: List[str] = []


class SingleSiteSyncResponse(BaseModel):
    """Response from single site sync."""

    success: bool
    ga4_records: int = 0
    gsc_records: int = 0
    inserted: int = 0
    error: Optional[str] = None


class ModelPerformance(BaseModel):
    """Model performance metrics."""

    ai_model_used: str
    article_count: int = 0
    avg_position: float = 0.0
    total_clicks: int = 0
    total_impressions: int = 0
    avg_cost: float = 0.0


class CostAnalysis(BaseModel):
    """Cost vs rank analysis."""

    correlation: float = 0.0
    avg_cost_top_10: float = 0.0
    avg_cost_10_20: float = 0.0
    avg_cost_below_20: float = 0.0
    recommendation: str = ""


class InsightsReport(BaseModel):
    """Comprehensive insights report."""

    workspace_id: str
    period_days: int
    model_performance: List[ModelPerformance] = []
    cost_analysis: CostAnalysis
    underperforming_clusters: List[dict] = []
    trending_topics: List[dict] = []
    declining_topics: List[dict] = []
    recommendations: List[str] = []


class AlertResponse(BaseModel):
    """Alert information."""

    id: str
    workspace_id: str
    alert_type: str
    level: str
    title: str
    message: str
    data: dict = {}
    created_at: str
    acknowledged: bool = False


class PerformanceCheckRequest(BaseModel):
    """Request to check performance and generate alerts."""

    clusters: List[dict] = Field(default_factory=list)
    declining: List[dict] = Field(default_factory=list)
    cost_analysis: dict = Field(default_factory=dict)


# Endpoints
@router.post("/sync", response_model=SyncResponse)
async def trigger_analytics_sync(request: SyncRequest):
    """
    Trigger analytics sync for workspaces.

    If workspace_id is provided, syncs only that workspace.
    Otherwise, syncs all active workspaces.
    """
    try:
        results = await sync_analytics_daily(workspace_id=request.workspace_id)

        return SyncResponse(
            success=len(results.get("errors", [])) == 0,
            message="Analytics sync completed",
            workspaces_processed=results.get("workspaces_processed", 0),
            sites_synced=results.get("sites_synced", 0),
            records_inserted=results.get("records_inserted", 0),
            errors=results.get("errors", []),
        )
    except Exception as e:
        logger.error(f"Failed to trigger analytics sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/site", response_model=SingleSiteSyncResponse)
async def sync_single_site_endpoint(request: SyncRequest):
    """
    Sync analytics for a single site.

    Requires site_url and workspace_id.
    """
    if not request.site_url or not request.workspace_id:
        raise HTTPException(
            status_code=400, detail="site_url and workspace_id are required"
        )

    try:
        results = await sync_single_site(
            workspace_id=request.workspace_id,
            site_url=request.site_url,
            ga_property_id=request.ga_property_id,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        return SingleSiteSyncResponse(
            success=results.get("success", False),
            ga4_records=results.get("ga4_records", 0),
            gsc_records=results.get("gsc_records", 0),
            inserted=results.get("inserted", 0),
            error=results.get("error"),
        )
    except Exception as e:
        logger.error(f"Failed to sync site: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/models", response_model=List[ModelPerformance])
async def get_model_performance(
    workspace_id: str = Query(..., description="Workspace ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
):
    """
    Get AI model performance analysis.

    Analyzes which AI models perform best in terms of search rankings.
    """
    try:
        results = await performance_analyzer.analyze_model_performance(
            workspace_id, days
        )
        return [ModelPerformance(**r) for r in results]
    except Exception as e:
        logger.error(f"Failed to get model performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/cost", response_model=CostAnalysis)
async def get_cost_analysis(
    workspace_id: str = Query(..., description="Workspace ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
):
    """
    Get cost vs rank analysis.

    Analyzes correlation between content generation cost and search rankings.
    """
    try:
        result = await performance_analyzer.analyze_cost_vs_rank(workspace_id, days)
        return CostAnalysis(**result)
    except Exception as e:
        logger.error(f"Failed to get cost analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/insights", response_model=InsightsReport)
async def get_insights_report(
    workspace_id: str = Query(..., description="Workspace ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
):
    """
    Get comprehensive insights report.

    Includes model performance, cost analysis, underperforming clusters,
    trending topics, and recommendations.
    """
    try:
        result = await performance_analyzer.generate_insights_report(workspace_id, days)
        return InsightsReport(
            workspace_id=result["workspace_id"],
            period_days=result["period_days"],
            model_performance=[
                ModelPerformance(**m) for m in result.get("model_performance", [])
            ],
            cost_analysis=CostAnalysis(**result.get("cost_analysis", {})),
            underperforming_clusters=result.get("underperforming_clusters", []),
            trending_topics=result.get("trending_topics", []),
            declining_topics=result.get("declining_topics", []),
            recommendations=result.get("recommendations", []),
        )
    except Exception as e:
        logger.error(f"Failed to get insights report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/clusters/{cluster_id}")
async def get_cluster_performance(
    cluster_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
):
    """
    Get performance metrics for a specific cluster.
    """
    try:
        result = await performance_analyzer.get_cluster_performance(cluster_id, days)
        return result
    except Exception as e:
        logger.error(f"Failed to get cluster performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/underperforming", response_model=List[dict])
async def get_underperforming_clusters(
    workspace_id: str = Query(..., description="Workspace ID"),
    position_threshold: float = Query(
        20.0, description="Position above which is considered poor"
    ),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
):
    """
    Get list of underperforming clusters.

    Returns clusters with average position above the threshold.
    """
    try:
        result = await performance_analyzer.get_underperforming_clusters(
            workspace_id, position_threshold, days
        )
        return result
    except Exception as e:
        logger.error(f"Failed to get underperforming clusters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/check", response_model=List[AlertResponse])
async def check_performance_alerts(
    workspace_id: str = Query(..., description="Workspace ID"),
    request: PerformanceCheckRequest = None,
):
    """
    Check for performance issues and generate alerts.

    Analyzes the provided performance data and generates alerts
    for any issues detected.
    """
    try:
        performance_data = {}
        if request:
            performance_data = {
                "clusters": request.clusters,
                "declining": request.declining,
                "cost_analysis": request.cost_analysis,
            }

        alerts = await alerting_engine.check_performance_issues(
            workspace_id, performance_data
        )

        return [
            AlertResponse(
                id=a.id,
                workspace_id=a.workspace_id,
                alert_type=a.alert_type.value,
                level=a.level.value,
                title=a.title,
                message=a.message,
                data=a.data,
                created_at=a.created_at,
                acknowledged=a.acknowledged,
            )
            for a in alerts
        ]
    except Exception as e:
        logger.error(f"Failed to check alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
