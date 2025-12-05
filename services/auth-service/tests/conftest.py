"""Pytest configuration and fixtures."""

import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# Set DATABASE_URL before importing models - required for SQLite compatibility in models
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.models.user import User
from main import app


# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


# Test settings
def get_test_settings() -> Settings:
    """Get test settings."""
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        JWT_SECRET_KEY="test-secret-key",
        ENCRYPTION_KEY="test-encryption-key-32bytes!",
        RABBITMQ_URL="amqp://guest:guest@localhost:5672/",
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


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for tests."""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        first_name="Test",
        last_name="User",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Create authorization headers with test user token."""
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}
