"""Scheduler API endpoints for content scheduling."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, get_current_user
from app.scheduler.scheduler import ContentScheduler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


class ScheduleJobRequest(BaseModel):
    """Request for scheduling a content generation job."""

    plan_id: UUID
    workspace_id: UUID
    scheduled_at: Optional[datetime] = None
    priority: str = Field(default="medium")


class ScheduledJobResponse(BaseModel):
    """Response for a scheduled job."""

    id: str
    plan_id: str
    workspace_id: str
    scheduled_at: datetime
    priority: str
    status: str
    created_at: datetime


class OptimalTimeResponse(BaseModel):
    """Response for optimal publishing times."""

    datetime: str
    day_of_week: int
    hour: int
    engagement_score: float
    recommended: bool


class TrafficPatternRequest(BaseModel):
    """Request for updating traffic patterns."""

    patterns: List[Dict[str, Any]]


@router.post("/jobs", response_model=ScheduledJobResponse, status_code=status.HTTP_201_CREATED)
async def schedule_job(
    request: ScheduleJobRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Schedule a content generation job.

    Jobs are processed by Celery workers based on their scheduled time.
    """
    scheduler = ContentScheduler()

    try:
        job = await scheduler.schedule_generation(
            plan_id=request.plan_id,
            workspace_id=request.workspace_id,
            scheduled_at=request.scheduled_at,
            priority=request.priority,
        )

        return ScheduledJobResponse(
            id=job.id,
            plan_id=str(job.plan_id),
            workspace_id=str(job.workspace_id),
            scheduled_at=job.scheduled_at,
            priority=job.priority,
            status=job.status,
            created_at=job.created_at,
        )

    except Exception as e:
        logger.error(f"Failed to schedule job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule job",
        )


@router.get("/jobs", response_model=List[ScheduledJobResponse])
async def list_pending_jobs(
    workspace_id: Optional[UUID] = None,
    limit: int = 100,
    current_user: CurrentUser = Depends(get_current_user),
):
    """List pending scheduled jobs."""
    scheduler = ContentScheduler()

    try:
        jobs = await scheduler.get_pending_jobs(
            workspace_id=workspace_id,
            limit=limit,
        )

        return [
            ScheduledJobResponse(
                id=job.id,
                plan_id=str(job.plan_id),
                workspace_id=str(job.workspace_id),
                scheduled_at=job.scheduled_at,
                priority=job.priority,
                status=job.status,
                created_at=job.created_at,
            )
            for job in jobs
        ]

    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list jobs",
        )


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_job(
    job_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Cancel a scheduled job."""
    scheduler = ContentScheduler()

    cancelled = await scheduler.cancel_job(job_id)
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or already processed",
        )


@router.get("/optimal-times", response_model=List[OptimalTimeResponse])
async def get_optimal_times(
    workspace_id: UUID,
    days_ahead: int = 7,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get optimal publishing times based on traffic patterns.

    Returns recommended times for publishing content based on
    historical traffic data and engagement patterns.
    """
    scheduler = ContentScheduler()

    try:
        times = await scheduler.get_optimal_times(
            workspace_id=workspace_id,
            days_ahead=days_ahead,
        )

        return [
            OptimalTimeResponse(
                datetime=t["datetime"],
                day_of_week=t["day_of_week"],
                hour=t["hour"],
                engagement_score=t["engagement_score"],
                recommended=t["recommended"],
            )
            for t in times
        ]

    except Exception as e:
        logger.error(f"Failed to get optimal times: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get optimal times",
        )


@router.post("/traffic-patterns/{workspace_id}")
async def update_traffic_patterns(
    workspace_id: UUID,
    request: TrafficPatternRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update traffic patterns for a workspace.

    Traffic patterns are used for smart scheduling to optimize
    content publication times.
    """
    scheduler = ContentScheduler()

    try:
        count = await scheduler.update_traffic_patterns(
            workspace_id=workspace_id,
            patterns=request.patterns,
        )

        return {"message": f"Updated {count} traffic patterns", "count": count}

    except Exception as e:
        logger.error(f"Failed to update traffic patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update traffic patterns",
        )
