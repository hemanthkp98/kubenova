"""
Pytest fixtures shared across the entire test suite.

Provides:
  - async_client: TestClient backed by the FastAPI app with in-memory SQLite
  - mock_k8s_clients: patch get_k8s_clients to return MagicMock objects
  - mock_llm_provider: a mock LLMProvider that returns canned responses
  - db_session: an in-memory SQLite AsyncSession for audit logger tests
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Use an in-memory SQLite database for tests.
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the whole test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a fresh in-memory SQLite session for each test function."""
    engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        # Import models to populate metadata.
        import app.core.audit.models  # noqa: F401
        await conn.run_sync(SQLModel.metadata.create_all)

    factory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def mock_k8s_clients():
    """
    Patch get_k8s_clients to return a dict of MagicMock API clients.

    Yields the mock dict so individual tests can configure return values.
    """
    core_mock = MagicMock()
    apps_mock = MagicMock()
    batch_mock = MagicMock()

    clients = {
        "core": core_mock,
        "apps": apps_mock,
        "batch": batch_mock,
        "networking": MagicMock(),
        "rbac": MagicMock(),
    }

    with patch("app.core.k8s.client.get_k8s_clients", return_value=clients):
        yield clients


@pytest.fixture
def mock_llm_provider():
    """Return a mock LLMProvider whose chat model returns canned AIMessages."""
    from langchain_core.messages import AIMessage

    mock_model = MagicMock()
    mock_model.invoke.return_value = AIMessage(content="Mock AI response")
    mock_model.bind_tools.return_value = mock_model
    mock_model.tool_calls = []

    provider = MagicMock()
    provider.get_chat_model.return_value = mock_model
    provider.is_available.return_value = True

    return provider


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an httpx AsyncClient backed by the FastAPI app.

    The database dependency is overridden to use the test in-memory session.
    """
    from app.api.deps import get_db
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
