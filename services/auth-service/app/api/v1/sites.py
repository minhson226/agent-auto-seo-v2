"""Site routes."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.site import SiteCreate, SiteResponse, SiteUpdate
from app.services.site_service import SiteService
from app.services.event_publisher import event_publisher

router = APIRouter(tags=["Sites"])


@router.get(
    "/workspaces/{workspace_id}/sites",
    response_model=List[SiteResponse],
)
async def list_sites(
    workspace_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all sites in a workspace."""
    site_service = SiteService(db)

    # Access check is done in the service
    try:
        sites = await site_service.get_workspace_sites(workspace_id, skip=skip, limit=limit)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    return [SiteResponse.model_validate(s) for s in sites]


@router.post(
    "/workspaces/{workspace_id}/sites",
    response_model=SiteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_site(
    workspace_id: UUID,
    site_create: SiteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new site in a workspace."""
    site_service = SiteService(db)

    try:
        site = await site_service.create(site_create, workspace_id, current_user.id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    # Publish event
    try:
        await event_publisher.publish(
            "site.created",
            {"site_id": site.id, "name": site.name, "domain": site.domain},
            workspace_id=workspace_id,
        )
    except Exception:
        pass

    return SiteResponse.model_validate(site)


@router.get("/sites/{site_id}", response_model=SiteResponse)
async def get_site(
    site_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific site."""
    site_service = SiteService(db)
    site = await site_service.get_by_id(site_id)

    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found",
        )

    # Check access
    from app.services.workspace_service import WorkspaceService
    workspace_service = WorkspaceService(db)
    if not await workspace_service.is_member(site.workspace_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace",
        )

    return SiteResponse.model_validate(site)


@router.put("/sites/{site_id}", response_model=SiteResponse)
async def update_site(
    site_id: UUID,
    site_update: SiteUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a site."""
    site_service = SiteService(db)

    try:
        site = await site_service.update(site_id, site_update, current_user.id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found",
        )

    return SiteResponse.model_validate(site)


@router.delete("/sites/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(
    site_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a site."""
    site_service = SiteService(db)

    try:
        deleted = await site_service.delete(site_id, current_user.id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Site not found",
        )
