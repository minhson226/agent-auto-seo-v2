"""Article model."""

import os
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func, BigInteger
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import JSON

from app.db.base import Base


def is_sqlite():
    """Check if using SQLite database."""
    db_url = os.environ.get("DATABASE_URL", "")
    return "sqlite" in db_url


# Use schema for PostgreSQL, skip for SQLite (testing)
def get_table_args():
    """Get table args with schema if not using SQLite."""
    if is_sqlite():
        return {}
    return {"schema": "autoseo"}


# Use JSONB for PostgreSQL, JSON for SQLite
def get_json_type():
    """Get JSON type based on database."""
    if is_sqlite():
        return JSON
    return JSONB


class Article(Base):
    """Model for generated articles."""

    __tablename__ = "articles"
    __table_args__ = get_table_args()

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # plan_id without FK constraint for SQLite test compatibility
    # In production with PostgreSQL, the FK is enforced by migration
    plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft")  # 'draft' | 'published' | 'archived'
    ai_model_used: Mapped[str] = mapped_column(String(100), default="gpt-3.5-turbo")
    cost_usd: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    generation_metadata: Mapped[dict] = mapped_column(
        "metadata", get_json_type(), default=dict, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    images: Mapped[List["ArticleImage"]] = relationship(
        "ArticleImage",
        back_populates="article",
        cascade="all, delete-orphan",
    )


def get_article_fk():
    """Get foreign key for article_id based on database."""
    if is_sqlite():
        return ForeignKey("articles.id", ondelete="CASCADE")
    return ForeignKey("autoseo.articles.id", ondelete="CASCADE")


class ArticleImage(Base):
    """Model for article images."""

    __tablename__ = "article_images"
    __table_args__ = get_table_args()

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        get_article_fk(),
        nullable=False,
        index=True
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    article: Mapped["Article"] = relationship(
        "Article",
        back_populates="images",
    )
