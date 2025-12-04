"""Content Scheduler service for managing scheduled content generation."""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class ScheduledJob:
    """Represents a scheduled content generation job."""

    id: str
    plan_id: UUID
    workspace_id: UUID
    scheduled_at: datetime
    priority: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    created_at: datetime
    metadata: Dict[str, Any]


@dataclass
class TrafficPattern:
    """Represents a traffic pattern for smart scheduling."""

    day_of_week: int  # 0=Monday, 6=Sunday
    hour: int  # 0-23
    engagement_score: float  # 0.0-1.0
    page_views: int
    avg_session_duration: float


class ContentScheduler:
    """Service for scheduling and managing content generation.

    Features:
    - Schedule content generation for specific times
    - Smart scheduling based on traffic patterns
    - Priority-based queue management
    - Retry logic for failed generations
    """

    def __init__(self, mock_mode: bool = False):
        """Initialize the content scheduler.

        Args:
            mock_mode: If True, operates in mock mode for testing
        """
        self._mock_mode = mock_mode
        self._scheduled_jobs: List[ScheduledJob] = []
        self._traffic_patterns: Dict[str, List[TrafficPattern]] = {}

    @property
    def mock_mode(self) -> bool:
        """Check if scheduler is in mock mode."""
        return self._mock_mode

    async def schedule_generation(
        self,
        plan_id: UUID,
        workspace_id: UUID,
        scheduled_at: Optional[datetime] = None,
        priority: str = "medium",
    ) -> ScheduledJob:
        """Schedule content generation for a plan.

        Args:
            plan_id: The content plan ID
            workspace_id: The workspace ID
            scheduled_at: When to generate (default: now)
            priority: Priority level ('high', 'medium', 'low')

        Returns:
            The scheduled job
        """
        now = datetime.now(timezone.utc)
        job = ScheduledJob(
            id=f"job-{len(self._scheduled_jobs) + 1}",
            plan_id=plan_id,
            workspace_id=workspace_id,
            scheduled_at=scheduled_at or now,
            priority=priority,
            status="pending",
            created_at=now,
            metadata={},
        )

        self._scheduled_jobs.append(job)
        logger.info(f"Scheduled job {job.id} for plan {plan_id} at {job.scheduled_at}")

        # In a real implementation, this would:
        # 1. Save to database
        # 2. If using Celery, schedule the task with eta

        return job

    async def get_pending_jobs(
        self,
        workspace_id: Optional[UUID] = None,
        limit: int = 100,
    ) -> List[ScheduledJob]:
        """Get pending scheduled jobs.

        Args:
            workspace_id: Optional filter by workspace
            limit: Maximum number of jobs to return

        Returns:
            List of pending jobs
        """
        now = datetime.now(timezone.utc)
        pending = [
            job
            for job in self._scheduled_jobs
            if job.status == "pending" and job.scheduled_at <= now
        ]

        if workspace_id:
            pending = [job for job in pending if job.workspace_id == workspace_id]

        # Sort by scheduled time and priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        pending.sort(
            key=lambda x: (x.scheduled_at, priority_order.get(x.priority, 1))
        )

        return pending[:limit]

    async def get_optimal_times(
        self,
        workspace_id: UUID,
        days_ahead: int = 7,
    ) -> List[Dict[str, Any]]:
        """Get optimal publishing times based on traffic patterns.

        Args:
            workspace_id: The workspace ID
            days_ahead: Number of days to look ahead

        Returns:
            List of optimal time slots with scores
        """
        patterns = self._traffic_patterns.get(str(workspace_id), [])

        if not patterns:
            # Return default optimal times if no data
            return self._get_default_optimal_times(days_ahead)

        # Calculate optimal times from patterns
        optimal_times = []
        now = datetime.now(timezone.utc)

        for day_offset in range(days_ahead):
            target_date = now + timedelta(days=day_offset)
            day_of_week = target_date.weekday()

            # Find best hours for this day
            day_patterns = [p for p in patterns if p.day_of_week == day_of_week]
            day_patterns.sort(key=lambda x: x.engagement_score, reverse=True)

            for pattern in day_patterns[:3]:  # Top 3 hours per day
                optimal_times.append({
                    "datetime": target_date.replace(
                        hour=pattern.hour, minute=0, second=0, microsecond=0
                    ).isoformat(),
                    "day_of_week": day_of_week,
                    "hour": pattern.hour,
                    "engagement_score": pattern.engagement_score,
                    "recommended": pattern.engagement_score >= 0.8,
                })

        return optimal_times

    def _get_default_optimal_times(self, days_ahead: int) -> List[Dict[str, Any]]:
        """Get default optimal times when no traffic data is available.

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            List of default optimal time slots
        """
        # Default optimal publishing times (based on general best practices)
        default_hours = {
            0: [9, 10, 14],   # Monday
            1: [9, 11, 15],   # Tuesday
            2: [9, 10, 14],   # Wednesday
            3: [10, 14, 16],  # Thursday
            4: [9, 11, 13],   # Friday
            5: [10, 11],      # Saturday
            6: [10, 11],      # Sunday
        }

        optimal_times = []
        now = datetime.now(timezone.utc)

        for day_offset in range(days_ahead):
            target_date = now + timedelta(days=day_offset)
            day_of_week = target_date.weekday()

            for hour in default_hours.get(day_of_week, [10]):
                score = 0.85 if day_of_week < 5 else 0.65  # Higher score on weekdays
                optimal_times.append({
                    "datetime": target_date.replace(
                        hour=hour, minute=0, second=0, microsecond=0
                    ).isoformat(),
                    "day_of_week": day_of_week,
                    "hour": hour,
                    "engagement_score": score,
                    "recommended": score >= 0.8,
                })

        return optimal_times

    async def update_traffic_patterns(
        self,
        workspace_id: UUID,
        patterns: List[Dict[str, Any]],
    ) -> int:
        """Update traffic patterns for a workspace.

        Args:
            workspace_id: The workspace ID
            patterns: List of traffic pattern data

        Returns:
            Number of patterns updated
        """
        parsed_patterns = []
        for p in patterns:
            try:
                parsed_patterns.append(
                    TrafficPattern(
                        day_of_week=p.get("day_of_week", 0),
                        hour=p.get("hour", 0),
                        engagement_score=p.get("engagement_score", 0.5),
                        page_views=p.get("page_views", 0),
                        avg_session_duration=p.get("avg_session_duration", 0.0),
                    )
                )
            except (KeyError, TypeError) as e:
                logger.warning(f"Invalid traffic pattern data: {e}")

        self._traffic_patterns[str(workspace_id)] = parsed_patterns
        logger.info(f"Updated {len(parsed_patterns)} traffic patterns for workspace {workspace_id}")

        return len(parsed_patterns)

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled job.

        Args:
            job_id: The job ID to cancel

        Returns:
            True if cancelled successfully
        """
        for job in self._scheduled_jobs:
            if job.id == job_id and job.status == "pending":
                job.status = "cancelled"
                logger.info(f"Cancelled job {job_id}")
                return True

        return False

    def clear_jobs(self):
        """Clear all scheduled jobs (for testing)."""
        self._scheduled_jobs = []

    def clear_patterns(self):
        """Clear all traffic patterns (for testing)."""
        self._traffic_patterns = {}


# Global scheduler instance
content_scheduler = ContentScheduler()
