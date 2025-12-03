"""Authentication schemas."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """JWT token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload schema."""

    sub: UUID
    type: str
    exp: int


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""

    refresh_token: str
