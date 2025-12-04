"""Tests for Scheduler functionality."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.scheduler.scheduler import ContentScheduler, ScheduledJob, TrafficPattern


class TestContentScheduler:
    """Tests for ContentScheduler class."""

    def test_initialization(self):
        """Test scheduler initialization."""
        scheduler = ContentScheduler(mock_mode=True)
        assert scheduler.mock_mode is True
        assert len(scheduler._scheduled_jobs) == 0

    @pytest.mark.asyncio
    async def test_schedule_generation(self):
        """Test scheduling a content generation job."""
        scheduler = ContentScheduler(mock_mode=True)

        plan_id = uuid4()
        workspace_id = uuid4()
        scheduled_at = datetime.now(timezone.utc) + timedelta(hours=1)

        job = await scheduler.schedule_generation(
            plan_id=plan_id,
            workspace_id=workspace_id,
            scheduled_at=scheduled_at,
            priority="high",
        )

        assert job.plan_id == plan_id
        assert job.workspace_id == workspace_id
        assert job.priority == "high"
        assert job.status == "pending"
        assert job.scheduled_at == scheduled_at

    @pytest.mark.asyncio
    async def test_schedule_generation_default_time(self):
        """Test scheduling with default time (now)."""
        scheduler = ContentScheduler(mock_mode=True)

        job = await scheduler.schedule_generation(
            plan_id=uuid4(),
            workspace_id=uuid4(),
        )

        # Should be scheduled for now
        assert job.scheduled_at is not None
        assert job.priority == "medium"  # default

    @pytest.mark.asyncio
    async def test_get_pending_jobs(self):
        """Test getting pending jobs."""
        scheduler = ContentScheduler(mock_mode=True)
        workspace_id = uuid4()

        # Schedule some jobs
        await scheduler.schedule_generation(
            plan_id=uuid4(),
            workspace_id=workspace_id,
            scheduled_at=datetime.now(timezone.utc) - timedelta(hours=1),  # Past, should be pending
        )
        await scheduler.schedule_generation(
            plan_id=uuid4(),
            workspace_id=workspace_id,
            scheduled_at=datetime.now(timezone.utc) + timedelta(hours=1),  # Future, not ready
        )

        pending = await scheduler.get_pending_jobs(workspace_id=workspace_id)

        # Only the past job should be pending
        assert len(pending) == 1

    @pytest.mark.asyncio
    async def test_get_pending_jobs_priority_order(self):
        """Test pending jobs are sorted by priority."""
        scheduler = ContentScheduler(mock_mode=True)
        workspace_id = uuid4()
        past_time = datetime.now(timezone.utc) - timedelta(hours=1)

        # Schedule jobs with different priorities
        await scheduler.schedule_generation(
            plan_id=uuid4(),
            workspace_id=workspace_id,
            scheduled_at=past_time,
            priority="low",
        )
        await scheduler.schedule_generation(
            plan_id=uuid4(),
            workspace_id=workspace_id,
            scheduled_at=past_time,
            priority="high",
        )
        await scheduler.schedule_generation(
            plan_id=uuid4(),
            workspace_id=workspace_id,
            scheduled_at=past_time,
            priority="medium",
        )

        pending = await scheduler.get_pending_jobs()

        # Should be sorted by time, then priority
        priorities = [job.priority for job in pending]
        assert priorities[0] == "high"

    @pytest.mark.asyncio
    async def test_get_optimal_times(self):
        """Test getting optimal publishing times."""
        scheduler = ContentScheduler(mock_mode=True)
        workspace_id = uuid4()

        times = await scheduler.get_optimal_times(
            workspace_id=workspace_id,
            days_ahead=7,
        )

        assert len(times) > 0
        for time in times:
            assert "datetime" in time
            assert "engagement_score" in time
            assert 0 <= time["engagement_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_update_traffic_patterns(self):
        """Test updating traffic patterns."""
        scheduler = ContentScheduler(mock_mode=True)
        workspace_id = uuid4()

        patterns = [
            {"day_of_week": 0, "hour": 9, "engagement_score": 0.95, "page_views": 1000, "avg_session_duration": 120.0},
            {"day_of_week": 1, "hour": 10, "engagement_score": 0.90, "page_views": 950, "avg_session_duration": 115.0},
        ]

        count = await scheduler.update_traffic_patterns(
            workspace_id=workspace_id,
            patterns=patterns,
        )

        assert count == 2

    @pytest.mark.asyncio
    async def test_optimal_times_with_patterns(self):
        """Test optimal times calculation with traffic patterns."""
        scheduler = ContentScheduler(mock_mode=True)
        workspace_id = uuid4()

        # Add traffic patterns
        patterns = [
            {"day_of_week": 0, "hour": 9, "engagement_score": 0.95, "page_views": 1000, "avg_session_duration": 120.0},
            {"day_of_week": 0, "hour": 14, "engagement_score": 0.80, "page_views": 800, "avg_session_duration": 100.0},
        ]
        await scheduler.update_traffic_patterns(workspace_id, patterns)

        times = await scheduler.get_optimal_times(
            workspace_id=workspace_id,
            days_ahead=7,
        )

        # Should include times based on patterns
        assert len(times) > 0

    @pytest.mark.asyncio
    async def test_cancel_job(self):
        """Test cancelling a job."""
        scheduler = ContentScheduler(mock_mode=True)

        job = await scheduler.schedule_generation(
            plan_id=uuid4(),
            workspace_id=uuid4(),
        )

        cancelled = await scheduler.cancel_job(job.id)
        assert cancelled is True

        # Try to cancel non-existent job
        cancelled = await scheduler.cancel_job("non-existent")
        assert cancelled is False

    def test_clear_jobs(self):
        """Test clearing all jobs."""
        scheduler = ContentScheduler(mock_mode=True)
        scheduler._scheduled_jobs = [ScheduledJob(
            id="test",
            plan_id=uuid4(),
            workspace_id=uuid4(),
            scheduled_at=datetime.now(timezone.utc),
            priority="medium",
            status="pending",
            created_at=datetime.now(timezone.utc),
            metadata={},
        )]

        scheduler.clear_jobs()

        assert len(scheduler._scheduled_jobs) == 0

    def test_clear_patterns(self):
        """Test clearing traffic patterns."""
        scheduler = ContentScheduler(mock_mode=True)
        scheduler._traffic_patterns = {"test": []}

        scheduler.clear_patterns()

        assert len(scheduler._traffic_patterns) == 0


class TestScheduledJob:
    """Tests for ScheduledJob dataclass."""

    def test_job_creation(self):
        """Test creating a scheduled job."""
        now = datetime.now(timezone.utc)
        job = ScheduledJob(
            id="job-1",
            plan_id=uuid4(),
            workspace_id=uuid4(),
            scheduled_at=now,
            priority="high",
            status="pending",
            created_at=now,
            metadata={"key": "value"},
        )

        assert job.id == "job-1"
        assert job.priority == "high"
        assert job.status == "pending"
        assert job.metadata == {"key": "value"}


class TestTrafficPattern:
    """Tests for TrafficPattern dataclass."""

    def test_pattern_creation(self):
        """Test creating a traffic pattern."""
        pattern = TrafficPattern(
            day_of_week=0,
            hour=9,
            engagement_score=0.95,
            page_views=1000,
            avg_session_duration=120.0,
        )

        assert pattern.day_of_week == 0
        assert pattern.hour == 9
        assert pattern.engagement_score == 0.95
        assert pattern.page_views == 1000
