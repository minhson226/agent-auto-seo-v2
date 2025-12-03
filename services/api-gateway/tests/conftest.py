"""Pytest configuration for API Gateway tests."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_redis():
    """Mock Redis connection."""
    with patch("app.middleware.rate_limit.redis") as mock:
        mock_client = AsyncMock()
        mock.from_url.return_value = mock_client
        mock_client.pipeline.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        yield mock_client
