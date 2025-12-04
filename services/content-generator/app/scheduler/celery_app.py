"""Celery application configuration."""

import logging
from typing import Optional

from celery import Celery

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def create_celery_app() -> Celery:
    """Create and configure Celery application.

    Returns:
        Configured Celery app instance
    """
    # Get broker URL from settings, default to Redis
    broker_url = getattr(settings, "CELERY_BROKER_URL", "redis://localhost:6379/0")
    result_backend = getattr(settings, "CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    app = Celery(
        "content_scheduler",
        broker=broker_url,
        backend=result_backend,
        include=["app.scheduler.tasks"],
    )

    # Configure Celery
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,  # 1 hour max task time
        task_soft_time_limit=3000,  # 50 minutes soft limit
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
    )

    # Configure periodic tasks (Celery Beat)
    app.conf.beat_schedule = {
        "generate-scheduled-articles": {
            "task": "app.scheduler.tasks.generate_scheduled_articles",
            "schedule": 300.0,  # Every 5 minutes
        },
        "optimize-schedule-hourly": {
            "task": "app.scheduler.tasks.smart_schedule_optimizer_task",
            "schedule": 3600.0,  # Every hour
        },
    }

    return app


# Create the Celery app instance
celery_app = create_celery_app()
