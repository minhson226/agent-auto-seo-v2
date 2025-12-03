"""Rate limiting middleware for API Gateway."""

import logging
from typing import Optional, Tuple
from uuid import UUID

import redis.asyncio as redis
from fastapi import HTTPException, Request, status
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RateLimiter:
    """Redis-based rate limiter."""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def is_rate_limited(
        self, key: str, limit: int, window_seconds: int = 60
    ) -> Tuple[bool, int]:
        """
        Check if a key is rate limited.

        Returns:
            Tuple of (is_limited, remaining_requests)
        """
        try:
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            results = await pipe.execute()
            current = results[0]
            remaining = max(0, limit - current)
            return current > limit, remaining
        except Exception as e:
            logger.warning(f"Rate limiting error: {e}")
            # Fail open - don't block requests if Redis is down
            return False, limit

    async def close(self):
        """Close Redis connection."""
        await self.redis.close()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health endpoints
        if request.url.path in ["/health", "/ready", "/metrics"]:
            return await call_next(request)

        # Extract user/workspace from JWT if present
        user_id, workspace_id = self._extract_token_info(request)

        # Determine rate limit key and limit
        if user_id:
            key = f"ratelimit:user:{user_id}:{request.url.path}"
            limit = settings.RATE_LIMIT_PER_USER_MINUTE
        else:
            # Use IP address for anonymous requests
            client_ip = request.client.host if request.client else "unknown"
            key = f"ratelimit:ip:{client_ip}:{request.url.path}"
            limit = settings.RATE_LIMIT_PER_USER_MINUTE // 2  # Lower limit for anonymous

        # Check rate limit
        is_limited, remaining = await self.rate_limiter.is_rate_limited(key, limit)

        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60", "X-RateLimit-Remaining": "0"},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = str(limit)

        return response

    def _extract_token_info(self, request: Request) -> Tuple[Optional[str], Optional[str]]:
        """Extract user_id and workspace_id from JWT token."""
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return None, None

        token = auth_header[7:]

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            user_id = payload.get("sub")
            workspace_id = payload.get("workspace_id")
            return user_id, workspace_id
        except JWTError:
            return None, None
