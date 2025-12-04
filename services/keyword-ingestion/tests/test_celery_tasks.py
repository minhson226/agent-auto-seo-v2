"""Tests for Celery tasks."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestCeleryTasks:
    """Tests for Celery task definitions."""

    def test_celery_app_configuration(self):
        """Test Celery app is configured correctly."""
        from app.tasks.celery_app import celery_app

        assert celery_app.main == "keyword_tasks"
        assert "task_serializer" in celery_app.conf
        assert celery_app.conf.task_serializer == "json"

    def test_celery_beat_schedule(self):
        """Test Celery beat schedule is defined."""
        from app.tasks.celery_app import celery_app

        assert "beat_schedule" in celery_app.conf
        schedule = celery_app.conf.beat_schedule
        assert "discover-trending-keywords-daily" in schedule
        assert "refresh-keyword-enrichment-weekly" in schedule

    def test_task_registration(self):
        """Test tasks are properly registered."""
        from app.tasks.keyword_tasks import (
            discover_trending_keywords,
            enrich_keywords_batch,
            pull_competitor_keywords,
        )

        assert enrich_keywords_batch.name is not None
        assert discover_trending_keywords.name is not None
        assert pull_competitor_keywords.name is not None

    def test_scheduled_tasks_exist(self):
        """Test scheduled tasks exist."""
        from app.tasks.keyword_tasks import (
            discover_trending_keywords_scheduled,
            refresh_keyword_enrichment_scheduled,
        )

        assert discover_trending_keywords_scheduled is not None
        assert refresh_keyword_enrichment_scheduled is not None

    def test_discover_trending_keywords_scheduled(self):
        """Test scheduled trending keywords task returns expected result."""
        from app.tasks.keyword_tasks import discover_trending_keywords_scheduled

        result = discover_trending_keywords_scheduled()
        assert result == {"status": "scheduled_run_completed"}

    def test_refresh_keyword_enrichment_scheduled(self):
        """Test scheduled enrichment refresh task returns expected result."""
        from app.tasks.keyword_tasks import refresh_keyword_enrichment_scheduled

        result = refresh_keyword_enrichment_scheduled()
        assert result == {"status": "scheduled_run_completed"}


class TestTaskImports:
    """Tests for task module imports."""

    def test_tasks_init_exports(self):
        """Test tasks __init__ exports correct items."""
        from app.tasks import (
            celery_app,
            discover_trending_keywords,
            enrich_keywords_batch,
            pull_competitor_keywords,
        )

        assert celery_app is not None
        assert enrich_keywords_batch is not None
        assert discover_trending_keywords is not None
        assert pull_competitor_keywords is not None
