"""JWT Security utilities."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        return None


def create_access_token(data: dict) -> str:
    """Create an access token for testing purposes."""
    to_encode = data.copy()
    to_encode["type"] = "access"
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
