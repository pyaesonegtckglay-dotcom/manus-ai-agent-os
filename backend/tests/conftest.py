"""Tests configuration and fixtures."""
import pytest
import asyncio
from typing import Generator
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_sandbox():
    """Mock E2B sandbox for testing."""
    sandbox = MagicMock()
    sandbox.id = "test-sandbox-123"
    sandbox.commands.run = AsyncMock(return_value=MagicMock(
        stdout="test output",
        stderr="",
        exit_code=0
    ))
    sandbox.files.read = AsyncMock(return_value=b"test content")
    sandbox.files.write = AsyncMock()
    sandbox.files.list = AsyncMock(return_value=[])
    return sandbox


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    client = MagicMock()
    client.table = MagicMock(return_value=MagicMock(
        select=MagicMock(return_value=MagicMock(
            execute=MagicMock(return_value=MagicMock(data=[]))
        )),
        insert=MagicMock(return_value=MagicMock(
            execute=MagicMock(return_value=MagicMock(data=[]))
        )),
        update=MagicMock(return_value=MagicMock(
            execute=MagicMock(return_value=MagicMock(data=[]))
        ))
    ))
    return client


@pytest.fixture
def mock_redis():
    """Mock Upstash Redis for testing."""
    redis = MagicMock()
    redis.ping = MagicMock(return_value=True)
    redis.zadd = MagicMock()
    redis.zrange = MagicMock(return_value=[])
    redis.hset = MagicMock()
    redis.hget = MagicMock(return_value=None)
    redis.hlen = MagicMock(return_value=0)
    return redis