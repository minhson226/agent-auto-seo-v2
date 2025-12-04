"""Background tasks for keyword automation."""

from app.tasks.celery_app import celery_app
from app.tasks.keyword_tasks import (
    discover_trending_keywords,
    enrich_keywords_batch,
    pull_competitor_keywords,
)

__all__ = [
    "celery_app",
    "enrich_keywords_batch",
    "discover_trending_keywords",
    "pull_competitor_keywords",
]
