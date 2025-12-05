"""Pytest configuration and fixtures.

This module configures the test environment to use mock implementations
of external services (ClickHouse) instead of real network calls.
"""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

# Set test environment variables before importing application modules
os.environ["CLICKHOUSE_HOST"] = "mock://localhost"
os.environ["CLICKHOUSE_PORT"] = "8123"
os.environ["CLICKHOUSE_USER"] = "test"
os.environ["CLICKHOUSE_PASSWORD"] = "test"
os.environ["CLICKHOUSE_DATABASE"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"

from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.db.clickhouse import clickhouse_client
from main import app


# Test settings - configured to use mock services
def get_test_settings() -> Settings:
    """Get test settings with mock service configurations."""
    return Settings(
        CLICKHOUSE_HOST="mock://localhost",
        CLICKHOUSE_PORT=8123,
        CLICKHOUSE_USER="test",
        CLICKHOUSE_PASSWORD="test",
        CLICKHOUSE_DATABASE="test",
        JWT_SECRET_KEY="test-secret-key",
    )


# Override settings for testing
app.dependency_overrides[get_settings] = get_test_settings


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def reset_clickhouse_mock():
    """Reset ClickHouse mock data before each test."""
    clickhouse_client._mock_mode = True
    clickhouse_client._connected = True
    clickhouse_client.clear_mock_data()
    yield
    clickhouse_client.clear_mock_data()


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def auth_headers() -> dict:
    """Create authorization headers with test token."""
    token = create_access_token(data={"sub": "test-user-id"})
    return {"Authorization": f"Bearer {token}"}
