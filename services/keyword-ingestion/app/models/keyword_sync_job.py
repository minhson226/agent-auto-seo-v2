"""KeywordSyncJob model for scheduled automation jobs."""

import os
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def get_table_args():
    """Get table args with schema if not using SQLite."""
    db_url = os.environ.get("DATABASE_URL", "")
    if "sqlite" in db_url:
        return {}
    return {"schema": "autoseo"}


def get_json_type():
    """Get JSON type based on database."""
    db_url = os.environ.get("DATABASE_URL", "")
    if "sqlite" in db_url:
        return JSON
    return JSONB


class KeywordSyncJob(Base):
    """Model for scheduled keyword automation jobs."""

    __tablename__ = "keyword_sync_jobs"
    __table_args__ = get_table_args()

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    job_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'trends', 'competitor', 'enrichment'
    schedule: Mapped[Optional[dict]] = mapped_column(
        get_json_type(), nullable=True
    )  # Cron schedule config
    config: Mapped[dict] = mapped_column(
        get_json_type(), default=dict, server_default="{}"
    )  # Job-specific config
    last_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="active"
    )  # 'active', 'paused', 'deleted'
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class KeywordJobRun(Base):
    """Model for keyword job execution history."""

    __tablename__ = "keyword_job_runs"
    __table_args__ = get_table_args()

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="running"
    )  # 'running', 'completed', 'failed'
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    keywords_processed: Mapped[int] = mapped_column(Integer, default=0)
    keywords_enriched: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_data: Mapped[dict] = mapped_column(
        get_json_type(), default=dict, server_default="{}"
    )
