"""
Async SQLite database engine and session management.

Uses aiosqlite + sqlmodel for async SQLite access. On startup, `create_tables()`
is called from the FastAPI lifespan to ensure the schema exists.
Postgres upgrade path: replace the engine URL in Settings.KUBENOVA_DATABASE_URL
with postgresql+asyncpg://user:pass@host/db and install asyncpg.
"""

from __future__ import annotations

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.config import get_settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Return (or lazily create) the shared async database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.KUBENOVA_DATABASE_URL,
            echo=settings.KUBENOVA_ENV == "development",
            connect_args={"check_same_thread": False},
        )

        # WAL mode allows concurrent readers + one writer, preventing
        # "database is locked" errors when the chat WebSocket and the
        # resource-panel polling write audit events simultaneously.
        @event.listens_for(_engine.sync_engine, "connect")
        def set_wal_mode(dbapi_conn, _):  # type: ignore[misc]
            dbapi_conn.execute("PRAGMA journal_mode=WAL")
            dbapi_conn.execute("PRAGMA busy_timeout=5000")

    return _engine


def get_async_session_factory() -> sessionmaker:  # type: ignore[type-arg]
    """Return a sessionmaker bound to the async engine."""
    return sessionmaker(
        bind=get_engine(),
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def create_tables() -> None:
    """Create all SQLModel-registered tables if they do not already exist."""
    # Import models so SQLModel metadata is populated before DDL runs.
    import app.core.audit.models  # noqa: F401

    async with get_engine().begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:  # type: ignore[return]
    """FastAPI dependency that yields an AsyncSession and commits/rolls back."""
    factory = get_async_session_factory()
    async with factory() as session:  # type: ignore[attr-defined]
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
