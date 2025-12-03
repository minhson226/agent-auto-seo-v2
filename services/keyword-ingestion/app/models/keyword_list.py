"""KeywordList model."""

import os
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


# Use schema for PostgreSQL, skip for SQLite (testing)
def get_table_args():
    """Get table args with schema if not using SQLite."""
    db_url = os.environ.get("DATABASE_URL", "")
    if "sqlite" in db_url:
        return {}
    return {"schema": "autoseo"}


class KeywordList(Base):
    """Model for keyword lists."""

    __tablename__ = "keyword_lists"
    __table_args__ = get_table_args()

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    total_keywords: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="processing")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    keywords: Mapped[List["Keyword"]] = relationship(
        "Keyword", back_populates="keyword_list", cascade="all, delete-orphan"
    )
