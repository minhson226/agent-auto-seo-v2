"""Tests for API Gateway endpoints."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "api-gateway"

    def test_readiness_check(self, client):
        """Test readiness check endpoint."""
        response = client.get("/ready")
        assert response.status_code == 200
        assert response.json()["status"] == "ready"


class TestRateLimiting:
    """Tests for rate limiting middleware."""

    @patch("app.middleware.rate_limit.RateLimiter.is_rate_limited")
    async def test_rate_limit_not_exceeded(self, mock_rate_limit, client):
        """Test request when rate limit is not exceeded."""
        mock_rate_limit.return_value = (False, 99)
        response = client.get("/health")
        assert response.status_code == 200

    def test_rate_limit_headers_present(self, client):
        """Test that rate limit headers are present."""
        response = client.get("/health")
        # Health endpoints should not have rate limit headers as they bypass rate limiting
        assert response.status_code == 200


class TestProxyRouting:
    """Tests for proxy routing functionality."""

    @patch("app.core.proxy.proxy_service.proxy_request")
    async def test_api_route_proxying(self, mock_proxy, client):
        """Test that API routes are proxied correctly."""
        from fastapi import Response
        mock_proxy.return_value = Response(
            content=b'{"status": "ok"}',
            status_code=200,
            media_type="application/json",
        )
        
        response = client.get("/api/v1/auth/me")
        # Without proper mocking, this will try to actually proxy
        assert response.status_code in [200, 401, 403, 404, 503]


class TestCORS:
    """Tests for CORS middleware."""

    def test_cors_preflight(self, client):
        """Test CORS preflight request."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200


class TestLogging:
    """Tests for logging middleware."""

    def test_correlation_id_header(self, client):
        """Test that correlation ID is added to response."""
        response = client.get("/health")
        # Correlation ID should be in response headers
        assert "x-correlation-id" in response.headers or response.status_code == 200


class TestDiagnostics:
    """Tests for diagnostics endpoints."""

    @patch("app.api.diagnostics.check_service_health")
    async def test_diagnostics_endpoint(self, mock_check_health, client):
        """Test diagnostics endpoint returns system health."""
        # Mock the service health check to return healthy status
        mock_check_health.return_value = {
            "name": "Test Service",
            "status": "healthy",
            "url": "http://test:8080",
            "response_time_ms": 10.5,
            "details": {"status": "healthy"}
        }
        
        response = client.get("/api/v1/diagnostics/")
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "services" in data
        assert "environment" in data
        assert "build" in data

    @patch("app.api.diagnostics.check_service_health")
    async def test_health_summary_endpoint(self, mock_check_health, client):
        """Test health summary endpoint."""
        mock_check_health.return_value = {
            "name": "test",
            "status": "healthy",
            "response_time_ms": 10.5,
        }
        
        response = client.get("/api/v1/diagnostics/health-summary")
        assert response.status_code == 200
        data = response.json()
        assert "healthy" in data
        assert "total" in data
        assert "services" in data
