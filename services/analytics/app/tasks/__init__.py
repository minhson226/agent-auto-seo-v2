"""Tasks package for scheduled data sync jobs."""

from app.tasks.sync_tasks import sync_analytics_daily

__all__ = ["sync_analytics_daily"]
