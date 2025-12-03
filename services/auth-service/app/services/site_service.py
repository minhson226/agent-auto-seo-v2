"""Site service for CRUD operations."""

import json
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encrypt_api_key, decrypt_api_key
from app.models.site import Site
from app.schemas.site import SiteCreate, SiteUpdate
from app.services.workspace_service import WorkspaceService


class SiteService:
    """Service for site-related operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.workspace_service = WorkspaceService(db)

    async def get_by_id(self, site_id: UUID) -> Optional[Site]:
        """Get a site by ID."""
        result = await self.db.execute(select(Site).where(Site.id == site_id))
        return result.scalar_one_or_none()

    async def get_workspace_sites(
        self, workspace_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Site]:
        """Get all sites in a workspace."""
        result = await self.db.execute(
            select(Site)
            .where(and_(Site.workspace_id == workspace_id, Site.is_active == True))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(
        self, site_create: SiteCreate, workspace_id: UUID, user_id: UUID
    ) -> Site:
        """Create a new site."""
        # Check workspace access
        if not await self.workspace_service.is_member(workspace_id, user_id):
            raise PermissionError("You don't have access to this workspace")

        # Encrypt WordPress credentials if provided
        api_credentials = {}
        if site_create.wp_credentials:
            api_credentials["wp_credentials_encrypted"] = encrypt_api_key(
                json.dumps(site_create.wp_credentials)
            )
        if site_create.wp_api_endpoint:
            api_credentials["wp_api_endpoint"] = site_create.wp_api_endpoint
        if site_create.wp_auth_type:
            api_credentials["wp_auth_type"] = site_create.wp_auth_type

        site = Site(
            workspace_id=workspace_id,
            name=site_create.name,
            domain=site_create.domain,
            platform=site_create.platform,
            settings=site_create.settings or {},
            api_credentials=api_credentials,
        )
        self.db.add(site)
        await self.db.commit()
        await self.db.refresh(site)
        return site

    async def update(
        self, site_id: UUID, site_update: SiteUpdate, user_id: UUID
    ) -> Optional[Site]:
        """Update a site."""
        site = await self.get_by_id(site_id)
        if not site:
            return None

        # Check workspace access
        if not await self.workspace_service.is_member(site.workspace_id, user_id):
            raise PermissionError("You don't have access to this workspace")

        update_data = site_update.model_dump(exclude_unset=True)

        # Handle credential updates
        if "wp_credentials" in update_data:
            credentials = update_data.pop("wp_credentials")
            if credentials:
                site.api_credentials["wp_credentials_encrypted"] = encrypt_api_key(
                    json.dumps(credentials)
                )

        if "wp_api_endpoint" in update_data:
            site.api_credentials["wp_api_endpoint"] = update_data.pop("wp_api_endpoint")

        if "wp_auth_type" in update_data:
            site.api_credentials["wp_auth_type"] = update_data.pop("wp_auth_type")

        for field, value in update_data.items():
            setattr(site, field, value)

        await self.db.commit()
        await self.db.refresh(site)
        return site

    async def delete(self, site_id: UUID, user_id: UUID) -> bool:
        """Delete a site."""
        site = await self.get_by_id(site_id)
        if not site:
            return False

        # Check workspace access
        if not await self.workspace_service.is_member(site.workspace_id, user_id):
            raise PermissionError("You don't have access to this workspace")

        await self.db.delete(site)
        await self.db.commit()
        return True

    def get_decrypted_credentials(self, site: Site) -> Optional[dict]:
        """Get decrypted WordPress credentials for a site."""
        if not site.api_credentials.get("wp_credentials_encrypted"):
            return None

        try:
            decrypted = decrypt_api_key(site.api_credentials["wp_credentials_encrypted"])
            return json.loads(decrypted)
        except Exception:
            return None
