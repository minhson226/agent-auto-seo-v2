"""Pytest configuration for integration tests."""

import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_workspace_id():
    """Generate a mock workspace ID."""
    from uuid import uuid4
    return str(uuid4())


@pytest.fixture
def mock_user_id():
    """Generate a mock user ID."""
    from uuid import uuid4
    return str(uuid4())
