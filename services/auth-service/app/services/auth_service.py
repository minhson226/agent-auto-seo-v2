"""Authentication service."""

from datetime import datetime, timezone
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate
from app.services.user_service import UserService


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)

    async def register(self, user_create: UserCreate) -> User:
        """Register a new user."""
        # Check if user already exists
        existing_user = await self.user_service.get_by_email(user_create.email)
        if existing_user:
            raise ValueError("User with this email already exists")

        return await self.user_service.create(user_create)

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password."""
        user = await self.user_service.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user

    async def login(self, email: str, password: str) -> Optional[Token]:
        """Login a user and return tokens."""
        user = await self.authenticate(email, password)
        if not user:
            return None

        # Update last login time
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()

        # Generate tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def refresh_tokens(self, refresh_token: str) -> Optional[Token]:
        """Refresh access token using refresh token."""
        payload = decode_token(refresh_token)
        if not payload:
            return None

        if payload.get("type") != "refresh":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        user = await self.user_service.get_by_id(user_id)
        if not user or not user.is_active:
            return None

        # Generate new tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    async def get_current_user(self, token: str) -> Optional[User]:
        """Get the current user from a token."""
        payload = decode_token(token)
        if not payload:
            return None

        if payload.get("type") != "access":
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        return await self.user_service.get_by_id(user_id)
