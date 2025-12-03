"""API Key service for managing encrypted API keys."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encrypt_api_key, decrypt_api_key
from app.models.api_key import ApiKey
from app.schemas.api_key import ApiKeyCreate
from app.services.workspace_service import WorkspaceService


class ApiKeyService:
    """Service for API key management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.workspace_service = WorkspaceService(db)

    async def get_by_id(self, api_key_id: UUID) -> Optional[ApiKey]:
        """Get an API key by ID."""
        result = await self.db.execute(select(ApiKey).where(ApiKey.id == api_key_id))
        return result.scalar_one_or_none()

    async def get_workspace_api_keys(
        self, workspace_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[ApiKey]:
        """Get all API keys for a workspace."""
        result = await self.db.execute(
            select(ApiKey)
            .where(ApiKey.workspace_id == workspace_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_service(
        self, workspace_id: UUID, service_name: str
    ) -> Optional[ApiKey]:
        """Get an API key by service name."""
        result = await self.db.execute(
            select(ApiKey).where(
                and_(
                    ApiKey.workspace_id == workspace_id,
                    ApiKey.service_name == service_name,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self, api_key_create: ApiKeyCreate, workspace_id: UUID, user_id: UUID
    ) -> ApiKey:
        """Create a new API key (encrypted)."""
        # Check workspace access
        if not await self.workspace_service.is_member(workspace_id, user_id):
            raise PermissionError("You don't have access to this workspace")

        # Check if key for this service already exists
        existing = await self.get_by_service(workspace_id, api_key_create.service_name)
        if existing:
            raise ValueError(
                f"API key for service '{api_key_create.service_name}' already exists"
            )

        # Encrypt the API key
        encrypted_key = encrypt_api_key(api_key_create.api_key)

        api_key = ApiKey(
            workspace_id=workspace_id,
            service_name=api_key_create.service_name,
            api_key_encrypted=encrypted_key,
            settings=api_key_create.settings or {},
        )
        self.db.add(api_key)
        await self.db.commit()
        await self.db.refresh(api_key)
        return api_key

    async def update(
        self,
        api_key_id: UUID,
        api_key_value: Optional[str],
        settings: Optional[dict],
        user_id: UUID,
    ) -> Optional[ApiKey]:
        """Update an API key."""
        api_key = await self.get_by_id(api_key_id)
        if not api_key:
            return None

        # Check workspace access
        if not await self.workspace_service.is_member(api_key.workspace_id, user_id):
            raise PermissionError("You don't have access to this workspace")

        if api_key_value:
            api_key.api_key_encrypted = encrypt_api_key(api_key_value)

        if settings is not None:
            api_key.settings = settings

        await self.db.commit()
        await self.db.refresh(api_key)
        return api_key

    async def delete(self, api_key_id: UUID, user_id: UUID) -> bool:
        """Delete an API key."""
        api_key = await self.get_by_id(api_key_id)
        if not api_key:
            return False

        # Check workspace access
        if not await self.workspace_service.is_member(api_key.workspace_id, user_id):
            raise PermissionError("You don't have access to this workspace")

        await self.db.delete(api_key)
        await self.db.commit()
        return True

    def decrypt_key(self, api_key: ApiKey) -> str:
        """Decrypt an API key value."""
        return decrypt_api_key(api_key.api_key_encrypted)
