"""
Shared FastAPI dependency functions.

These are injected into route handlers via FastAPI's Depends() mechanism.
Keep business logic out of this module — it should only wire dependencies.
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit.logger import AuditLogger, audit_logger
from app.core.k8s.multi_cluster import ClusterManager, cluster_manager
from app.core.llm.factory import LLMProvider, get_llm_provider
from app.db.database import get_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for the duration of the request."""
    async for session in get_session():  # type: ignore[attr-defined]
        yield session


def get_cluster_manager() -> ClusterManager:
    """Return the global ClusterManager singleton."""
    return cluster_manager


def get_audit_logger() -> AuditLogger:
    """Return the global AuditLogger singleton."""
    return audit_logger


def get_llm() -> LLMProvider:
    """Return the LLM provider configured via application settings."""
    return get_llm_provider()
