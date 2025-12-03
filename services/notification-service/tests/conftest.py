"""Pytest configuration for Notification Service tests."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_rabbitmq():
    """Mock RabbitMQ connection."""
    with patch("app.services.event_consumer.aio_pika") as mock:
        mock.connect_robust = AsyncMock()
        yield mock
