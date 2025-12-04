"""ContentPlan model."""

import os
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import JSON

from app.db.base import Base


# Use schema for PostgreSQL, skip for SQLite (testing)
def get_table_args():
    """Get table args with schema if not using SQLite."""
    db_url = os.environ.get("DATABASE_URL", "")
    if "sqlite" in db_url:
        return {}
    return {"schema": "autoseo"}


# Use JSONB for PostgreSQL, JSON for SQLite
def get_json_type():
    """Get JSON type based on database."""
    db_url = os.environ.get("DATABASE_URL", "")
    if "sqlite" in db_url:
        return JSON
    return JSONB


def get_foreign_key_reference(table: str):
    """Get foreign key reference with schema qualification."""
    db_url = os.environ.get("DATABASE_URL", "")
    if "sqlite" in db_url:
        return f"{table}.id"
    return f"autoseo.{table}.id"


class ContentPlan(Base):
    """Model for content plans."""

    __tablename__ = "content_plans"
    __table_args__ = get_table_args()

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    cluster_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_foreign_key_reference("topic_clusters"), ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # 'high' | 'medium' | 'low'
    # Store target_keywords as JSON for SQLite compatibility
    target_keywords_json: Mapped[Optional[dict]] = mapped_column(
        "target_keywords", get_json_type(), default=list, server_default="[]"
    )
    competitors_data: Mapped[dict] = mapped_column(
        get_json_type(), default=dict, server_default="{}"
    )
    status: Mapped[str] = mapped_column(String(50), default="draft")  # 'draft' | 'approved' | 'in_progress' | 'completed'
    estimated_word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    cluster: Mapped[Optional["TopicCluster"]] = relationship(
        "TopicCluster",
        back_populates="content_plans",
    )

    @property
    def target_keywords(self) -> List[str]:
        """Get target keywords as list."""
        if self.target_keywords_json is None:
            return []
        if isinstance(self.target_keywords_json, list):
            return self.target_keywords_json
        return []

    @target_keywords.setter
    def target_keywords(self, value: List[str]):
        """Set target keywords from list."""
        self.target_keywords_json = value if value else []
