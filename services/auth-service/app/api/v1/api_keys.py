"""API Key routes."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.api_key import ApiKeyCreate, ApiKeyResponse
from app.services.api_key_service import ApiKeyService

router = APIRouter(tags=["API Keys"])


@router.get(
    "/workspaces/{workspace_id}/api-keys",
    response_model=List[ApiKeyResponse],
)
async def list_api_keys(
    workspace_id: UUID,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys for a workspace."""
    api_key_service = ApiKeyService(db)

    # Check workspace access
    from app.services.workspace_service import WorkspaceService

    workspace_service = WorkspaceService(db)
    if not await workspace_service.is_member(workspace_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace",
        )

    api_keys = await api_key_service.get_workspace_api_keys(
        workspace_id, skip=skip, limit=limit
    )
    return [ApiKeyResponse.model_validate(k) for k in api_keys]


@router.post(
    "/workspaces/{workspace_id}/api-keys",
    response_model=ApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    workspace_id: UUID,
    api_key_create: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new API key for a workspace."""
    api_key_service = ApiKeyService(db)

    try:
        api_key = await api_key_service.create(
            api_key_create, workspace_id, current_user.id
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return ApiKeyResponse.model_validate(api_key)


@router.get("/api-keys/{api_key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    api_key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific API key (without the actual key value)."""
    api_key_service = ApiKeyService(db)
    api_key = await api_key_service.get_by_id(api_key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    # Check workspace access
    from app.services.workspace_service import WorkspaceService

    workspace_service = WorkspaceService(db)
    if not await workspace_service.is_member(api_key.workspace_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this workspace",
        )

    return ApiKeyResponse.model_validate(api_key)


@router.delete("/api-keys/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an API key."""
    api_key_service = ApiKeyService(db)

    try:
        deleted = await api_key_service.delete(api_key_id, current_user.id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
