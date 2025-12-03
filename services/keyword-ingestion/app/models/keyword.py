"""Keyword model."""

import os
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

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


class Keyword(Base):
    """Model for individual keywords."""

    __tablename__ = "keywords"
    __table_args__ = get_table_args()

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    list_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("keyword_lists.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_text: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    intent: Mapped[str] = mapped_column(String(50), default="unknown")
    search_volume: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    keyword_difficulty: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
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
    keyword_list: Mapped["KeywordList"] = relationship(
        "KeywordList", back_populates="keywords"
    )
