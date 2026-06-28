"""
Audit log SQLModel table and Pydantic read schemas.

AuditEvent is the persistent record written for every user interaction.
It deliberately omits API keys and LLM responses to keep the log
focused on operator actions and cluster changes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Text
from sqlmodel import Field as SMField, SQLModel


class AuditEvent(SQLModel, table=True):
    """Persistent audit log entry stored in SQLite."""

    __tablename__ = "audit_events"

    id: str = SMField(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        index=True,
    )
    timestamp: datetime = SMField(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    session_id: str = SMField(index=True)
    user_intent: str = SMField(sa_column=Column(Text))
    cluster_context: str = SMField(index=True)
    namespace: str = SMField(default="default")
    generated_command: str | None = SMField(default=None, sa_column=Column(Text, nullable=True))
    risk_level: str = SMField(default="LOW", index=True)
    dry_run_result: str | None = SMField(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="JSON-serialised DryRunResult.",
    )
    approved: bool | None = SMField(
        default=None,
        description="None=pending, True=approved, False=rejected.",
    )
    execution_result: str | None = SMField(
        default=None,
        sa_column=Column(Text, nullable=True),
        description="JSON-serialised ApplyResult.",
    )
    error: str | None = SMField(default=None, sa_column=Column(Text, nullable=True))


# ---------------------------------------------------------------------------
# Pydantic read schemas
# ---------------------------------------------------------------------------


class AuditEventRead(BaseModel):
    """Pydantic schema for returning audit events through the API."""

    id: str
    timestamp: datetime
    session_id: str
    user_intent: str
    cluster_context: str
    namespace: str
    generated_command: str | None = None
    risk_level: str
    dry_run_result: Any | None = None
    approved: bool | None = None
    execution_result: Any | None = None
    error: str | None = None

    model_config = {"from_attributes": True}


class AuditEventCreate(BaseModel):
    """Pydantic schema for writing a new audit event."""

    session_id: str
    user_intent: str
    cluster_context: str
    namespace: str = "default"
    generated_command: str | None = None
    risk_level: str = "LOW"
    dry_run_result: Any | None = None
    approved: bool | None = None
    execution_result: Any | None = None
    error: str | None = None


class PaginatedAuditEvents(BaseModel):
    """Paginated response for GET /audit."""

    items: list[AuditEventRead]
    total: int
    page: int
    page_size: int
    total_pages: int = Field(description="Ceiling of total / page_size.")
