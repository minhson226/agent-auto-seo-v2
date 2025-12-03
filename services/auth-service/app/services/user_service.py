"""User service for CRUD operations."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service for user-related operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination."""
        result = await self.db.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, user_create: UserCreate) -> User:
        """Create a new user."""
        user = User(
            email=user_create.email,
            password_hash=get_password_hash(user_create.password),
            first_name=user_create.first_name,
            last_name=user_create.last_name,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: UUID, user_update: UserUpdate) -> Optional[User]:
        """Update a user."""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        update_data = user_update.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["password_hash"] = get_password_hash(update_data.pop("password"))

        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user_id: UUID) -> bool:
        """Delete a user."""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        await self.db.delete(user)
        await self.db.commit()
        return True

    async def activate(self, user_id: UUID) -> Optional[User]:
        """Activate a user."""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        user.is_active = True
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def deactivate(self, user_id: UUID) -> Optional[User]:
        """Deactivate a user."""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        user.is_active = False
        await self.db.commit()
        await self.db.refresh(user)
        return user
