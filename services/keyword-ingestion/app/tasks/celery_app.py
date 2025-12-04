"""Celery application configuration."""

import os
from celery import Celery

# Get Redis URL from environment or use default
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "keyword_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.keyword_tasks"],
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3000,  # 50 min soft limit
    
    # Result settings
    result_expires=86400,  # 24 hours
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "discover-trending-keywords-daily": {
            "task": "app.tasks.keyword_tasks.discover_trending_keywords_scheduled",
            "schedule": 86400.0,  # Daily (24 hours)
        },
        "refresh-keyword-enrichment-weekly": {
            "task": "app.tasks.keyword_tasks.refresh_keyword_enrichment_scheduled",
            "schedule": 604800.0,  # Weekly (7 days)
        },
    },
)
