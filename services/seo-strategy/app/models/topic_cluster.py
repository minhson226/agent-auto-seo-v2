"""TopicCluster model."""

import os
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
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


class TopicCluster(Base):
    """Model for topic clusters."""

    __tablename__ = "topic_clusters"
    __table_args__ = get_table_args()

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), default="cluster")  # 'pillar' | 'cluster'
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pillar_cluster_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_foreign_key_reference("topic_clusters"), ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    metadata_: Mapped[dict] = mapped_column(
        "metadata", get_json_type(), default=dict, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    pillar_cluster: Mapped[Optional["TopicCluster"]] = relationship(
        "TopicCluster",
        back_populates="child_clusters",
        remote_side=[id],
    )
    child_clusters: Mapped[List["TopicCluster"]] = relationship(
        "TopicCluster",
        back_populates="pillar_cluster",
    )
    cluster_keywords: Mapped[List["ClusterKeyword"]] = relationship(
        "ClusterKeyword",
        back_populates="cluster",
        cascade="all, delete-orphan",
    )
    content_plans: Mapped[List["ContentPlan"]] = relationship(
        "ContentPlan",
        back_populates="cluster",
    )


class ClusterKeyword(Base):
    """Model for cluster-keyword associations."""

    __tablename__ = "cluster_keywords"
    __table_args__ = get_table_args()

    cluster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_foreign_key_reference("topic_clusters"), ondelete="CASCADE"),
        primary_key=True,
    )
    keyword_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )
    is_primary: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    cluster: Mapped["TopicCluster"] = relationship(
        "TopicCluster",
        back_populates="cluster_keywords",
    )
