"""Content Scheduler module for automated article generation."""

from app.scheduler.scheduler import ContentScheduler

# Celery tasks are optional - only import if celery is properly configured
try:
    from app.scheduler.celery_app import celery_app
    from app.scheduler.tasks import (
        generate_scheduled_articles,
        smart_schedule_optimizer_task,
        generate_article_task,
    )
    CELERY_AVAILABLE = True
except ImportError:
    celery_app = None
    generate_scheduled_articles = None
    smart_schedule_optimizer_task = None
    generate_article_task = None
    CELERY_AVAILABLE = False

__all__ = [
    "celery_app",
    "generate_scheduled_articles",
    "smart_schedule_optimizer_task",
    "generate_article_task",
    "ContentScheduler",
    "CELERY_AVAILABLE",
]
