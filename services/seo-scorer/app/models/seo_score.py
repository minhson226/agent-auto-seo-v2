"""SEO Score model."""

import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import JSON

from app.core.constants import DEFAULT_CHECKLIST
from app.db.base import Base


def _is_sqlite() -> bool:
    """Check if using SQLite database."""
    db_url = os.environ.get("DATABASE_URL", "")
    return "sqlite" in db_url


# Use schema for PostgreSQL, skip for SQLite (testing)
def get_table_args():
    """Get table args with schema if not using SQLite."""
    if _is_sqlite():
        return {}
    return {"schema": "autoseo"}


# Use JSONB for PostgreSQL, JSON for SQLite
def get_json_type():
    """Get JSON type based on database."""
    if _is_sqlite():
        return JSON
    return JSONB


class SeoScore(Base):
    """Model for SEO scores."""

    __tablename__ = "seo_scores"
    __table_args__ = get_table_args()

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Note: For SQLite testing, we skip foreign key constraint
    # In production with PostgreSQL, the migration handles the FK constraint
    article_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    manual_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    auto_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    checklist: Mapped[Dict[str, Any]] = mapped_column(
        get_json_type(), default=DEFAULT_CHECKLIST.copy
    )
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )  # 'pending' | 'completed' | 'reviewed'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def calculate_score(self) -> int:
        """Calculate score based on checklist items.
        
        Returns score as percentage (0-100).
        """
        if not self.checklist:
            return 0
        
        total_items = len(self.checklist)
        if total_items == 0:
            return 0
        
        checked_items = sum(1 for value in self.checklist.values() if value is True)
        return int((checked_items / total_items) * 100)
