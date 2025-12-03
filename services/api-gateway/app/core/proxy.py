"""Proxy service for forwarding requests to backend services."""

import logging
from typing import Dict, Optional

import httpx
from fastapi import Request, Response

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ProxyService:
    """Service for proxying requests to backend services."""

    SERVICE_ROUTES: Dict[str, str] = {
        "/api/v1/auth": settings.AUTH_SERVICE_URL,
        "/api/v1/workspaces": settings.AUTH_SERVICE_URL,
        "/api/v1/sites": settings.AUTH_SERVICE_URL,
        "/api/v1/api-keys": settings.AUTH_SERVICE_URL,
        "/api/v1/notifications": settings.NOTIFICATION_SERVICE_URL,
    }

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def get_target_url(self, path: str) -> Optional[str]:
        """Get the target service URL for a given path."""
        for route_prefix, service_url in self.SERVICE_ROUTES.items():
            if path.startswith(route_prefix):
                return service_url
        return None

    async def proxy_request(self, request: Request) -> Response:
        """Proxy a request to the appropriate backend service."""
        target_base_url = self.get_target_url(request.url.path)

        if not target_base_url:
            return Response(
                content='{"detail": "Service not found"}',
                status_code=404,
                media_type="application/json",
            )

        # Build target URL
        target_url = f"{target_base_url}{request.url.path}"
        if request.url.query:
            target_url += f"?{request.url.query}"

        # Forward headers (excluding host)
        headers = dict(request.headers)
        headers.pop("host", None)

        # Add correlation ID if present
        if hasattr(request.state, "correlation_id"):
            headers["X-Correlation-ID"] = request.state.correlation_id

        try:
            # Get request body
            body = await request.body()

            # Make request to backend service
            response = await self.client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )

            # Return response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )

        except httpx.TimeoutException:
            logger.error(f"Timeout proxying request to {target_url}")
            return Response(
                content='{"detail": "Service timeout"}',
                status_code=504,
                media_type="application/json",
            )
        except httpx.RequestError as e:
            logger.error(f"Error proxying request to {target_url}: {e}")
            return Response(
                content='{"detail": "Service unavailable"}',
                status_code=503,
                media_type="application/json",
            )


# Global proxy service instance
proxy_service = ProxyService()
