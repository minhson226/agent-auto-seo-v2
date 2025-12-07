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
        # Auth Service - Authentication, Workspaces, Sites, API Keys
        "/api/v1/auth": settings.AUTH_SERVICE_URL,
        "/api/v1/workspaces": settings.AUTH_SERVICE_URL,
        "/api/v1/sites": settings.AUTH_SERVICE_URL,
        "/api/v1/api-keys": settings.AUTH_SERVICE_URL,
        
        # Notification Service
        "/api/v1/notifications": settings.NOTIFICATION_SERVICE_URL,
        
        # Keyword Ingestion Service - Keywords, Keyword Lists, Automation, Intent
        "/api/v1/keyword-lists": settings.KEYWORD_INGESTION_URL,
        "/api/v1/keywords": settings.KEYWORD_INGESTION_URL,
        "/api/v1/keyword-automation": settings.KEYWORD_INGESTION_URL,
        "/api/v1/intent": settings.KEYWORD_INGESTION_URL,
        
        # SEO Strategy Service - Topic Clusters, Content Plans, ML Automation
        "/api/v1/topic-clusters": settings.SEO_STRATEGY_URL,
        "/api/v1/content-plans": settings.SEO_STRATEGY_URL,
        "/api/v1/ml-automation": settings.SEO_STRATEGY_URL,
        
        # Content Generator Service - Articles, LLM, Images, Scheduler, RAG, Publishing
        "/api/v1/articles": settings.CONTENT_GENERATOR_URL,
        "/api/v1/llm": settings.CONTENT_GENERATOR_URL,
        "/api/v1/images": settings.CONTENT_GENERATOR_URL,
        "/api/v1/scheduler": settings.CONTENT_GENERATOR_URL,
        "/api/v1/rag": settings.CONTENT_GENERATOR_URL,
        "/api/v1/publishing": settings.CONTENT_GENERATOR_URL,
        
        # SEO Scorer Service - SEO Scores, Auto Scoring
        "/api/v1/seo-scores": settings.SEO_SCORER_URL,
        "/api/v1/auto-scoring": settings.SEO_SCORER_URL,
        
        # Analytics Service - Analytics, Strategic Learning
        "/api/v1/analytics": settings.ANALYTICS_URL,
        "/api/v1/strategic-learning": settings.ANALYTICS_URL,
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
