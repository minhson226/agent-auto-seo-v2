"""API Key model."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database_utils import get_foreign_key_reference, get_json_type, get_table_args
from app.db.base import Base


class ApiKey(Base):
    """API Key model for storing encrypted external API keys."""

    __tablename__ = "api_keys"
    __table_args__ = get_table_args()

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(get_foreign_key_reference("workspaces"), ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g., 'openai', 'google', 'ahrefs'
    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    settings: Mapped[Optional[dict]] = mapped_column(get_json_type(), default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    workspace = relationship("Workspace", back_populates="api_keys")
