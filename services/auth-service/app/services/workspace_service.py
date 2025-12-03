"""Workspace service for CRUD operations."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.workspace import Workspace, WorkspaceMember
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate, WorkspaceUpdate, WorkspaceMemberCreate


class WorkspaceService:
    """Service for workspace-related operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, workspace_id: UUID) -> Optional[Workspace]:
        """Get a workspace by ID."""
        result = await self.db.execute(
            select(Workspace)
            .options(selectinload(Workspace.members))
            .where(Workspace.id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Workspace]:
        """Get a workspace by slug."""
        result = await self.db.execute(
            select(Workspace).where(Workspace.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_user_workspaces(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Workspace]:
        """Get all workspaces a user has access to."""
        # Get workspaces where user is owner
        owned_query = select(Workspace).where(
            and_(Workspace.owner_id == user_id, Workspace.is_active == True)
        )

        # Get workspaces where user is a member
        member_query = (
            select(Workspace)
            .join(WorkspaceMember)
            .where(
                and_(
                    WorkspaceMember.user_id == user_id,
                    Workspace.is_active == True,
                )
            )
        )

        # Union both queries
        from sqlalchemy import union_all

        union_query = union_all(owned_query, member_query).subquery()
        result = await self.db.execute(
            select(Workspace)
            .where(Workspace.id.in_(select(union_query.c.id)))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().unique().all())

    async def create(
        self, workspace_create: WorkspaceCreate, owner_id: UUID
    ) -> Workspace:
        """Create a new workspace."""
        workspace = Workspace(
            name=workspace_create.name,
            slug=workspace_create.slug,
            description=workspace_create.description,
            settings=workspace_create.settings or {},
            owner_id=owner_id,
        )
        self.db.add(workspace)
        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def update(
        self, workspace_id: UUID, workspace_update: WorkspaceUpdate, user_id: UUID
    ) -> Optional[Workspace]:
        """Update a workspace."""
        workspace = await self.get_by_id(workspace_id)
        if not workspace:
            return None

        # Check if user is the owner
        if workspace.owner_id != user_id:
            raise PermissionError("Only the owner can update the workspace")

        update_data = workspace_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(workspace, field, value)

        await self.db.commit()
        await self.db.refresh(workspace)
        return workspace

    async def delete(self, workspace_id: UUID, user_id: UUID) -> bool:
        """Delete a workspace."""
        workspace = await self.get_by_id(workspace_id)
        if not workspace:
            return False

        # Check if user is the owner
        if workspace.owner_id != user_id:
            raise PermissionError("Only the owner can delete the workspace")

        await self.db.delete(workspace)
        await self.db.commit()
        return True

    async def add_member(
        self, workspace_id: UUID, member_create: WorkspaceMemberCreate, owner_id: UUID
    ) -> WorkspaceMember:
        """Add a member to a workspace."""
        workspace = await self.get_by_id(workspace_id)
        if not workspace:
            raise ValueError("Workspace not found")

        if workspace.owner_id != owner_id:
            raise PermissionError("Only the owner can add members")

        # Check if member already exists
        result = await self.db.execute(
            select(WorkspaceMember).where(
                and_(
                    WorkspaceMember.workspace_id == workspace_id,
                    WorkspaceMember.user_id == member_create.user_id,
                )
            )
        )
        if result.scalar_one_or_none():
            raise ValueError("User is already a member of this workspace")

        member = WorkspaceMember(
            workspace_id=workspace_id,
            user_id=member_create.user_id,
            role=member_create.role,
        )
        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)
        return member

    async def remove_member(
        self, workspace_id: UUID, user_id: UUID, owner_id: UUID
    ) -> bool:
        """Remove a member from a workspace."""
        workspace = await self.get_by_id(workspace_id)
        if not workspace:
            return False

        if workspace.owner_id != owner_id:
            raise PermissionError("Only the owner can remove members")

        result = await self.db.execute(
            select(WorkspaceMember).where(
                and_(
                    WorkspaceMember.workspace_id == workspace_id,
                    WorkspaceMember.user_id == user_id,
                )
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            return False

        await self.db.delete(member)
        await self.db.commit()
        return True

    async def get_members(self, workspace_id: UUID) -> List[WorkspaceMember]:
        """Get all members of a workspace."""
        result = await self.db.execute(
            select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id)
        )
        return list(result.scalars().all())

    async def is_member(self, workspace_id: UUID, user_id: UUID) -> bool:
        """Check if a user is a member of a workspace (including owner)."""
        workspace = await self.get_by_id(workspace_id)
        if not workspace:
            return False

        if workspace.owner_id == user_id:
            return True

        result = await self.db.execute(
            select(WorkspaceMember).where(
                and_(
                    WorkspaceMember.workspace_id == workspace_id,
                    WorkspaceMember.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none() is not None
