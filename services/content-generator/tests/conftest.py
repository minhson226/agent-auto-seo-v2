"""Pytest configuration and fixtures."""

import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch
from uuid import uuid4

# Set DATABASE_URL before importing models
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from main import app


# Test settings
def get_test_settings() -> Settings:
    """Get test settings."""
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET_KEY="test-secret-key",
        RABBITMQ_URL="amqp://guest:guest@localhost:5672/",
        OPENAI_API_KEY="test-openai-key",
        S3_ENDPOINT="http://localhost:9002",
        S3_ACCESS_KEY="minioadmin",
        S3_SECRET_KEY="minioadmin_secret",
    )


# Override settings for testing
app.dependency_overrides[get_settings] = get_test_settings


# Create test database engine
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True, scope="function")
def setup_database(event_loop):
    """Set up test database before each test."""
    async def _setup():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def _teardown():
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    event_loop.run_until_complete(_setup())
    yield
    event_loop.run_until_complete(_teardown())


async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
    """Get test database session."""
    async with TestSessionLocal() as session:
        yield session


# Override database dependency
app.dependency_overrides[get_db] = get_test_db


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


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for tests."""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
def test_user_id():
    """Generate a test user ID."""
    return uuid4()


@pytest.fixture
def auth_headers(test_user_id) -> dict:
    """Create authorization headers with test user token."""
    token = create_access_token(data={"sub": str(test_user_id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_workspace_id():
    """Generate a test workspace ID."""
    return uuid4()
