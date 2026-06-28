"""
Asynchronous audit logger.

AuditLogger provides async methods for writing, querying, and exporting
audit events. It is instantiated once at startup and injected as a FastAPI
dependency via app.api.deps.
"""

from __future__ import annotations

import csv
import io
import json
import math
from datetime import datetime
from typing import Any

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit.models import AuditEvent, AuditEventCreate, AuditEventRead, PaginatedAuditEvents


class AuditLogger:
    """Async helper for writing and querying the audit log."""

    async def write(
        self, session: AsyncSession, event: AuditEventCreate
    ) -> AuditEventRead:
        """
        Persist a new audit event and return its read representation.

        Args:
            session: Active AsyncSession.
            event: Data for the new event.

        Returns:
            AuditEventRead with the generated ID and timestamp.
        """
        db_event = AuditEvent(
            session_id=event.session_id,
            user_intent=event.user_intent,
            cluster_context=event.cluster_context,
            namespace=event.namespace,
            generated_command=event.generated_command,
            risk_level=event.risk_level,
            dry_run_result=json.dumps(event.dry_run_result) if event.dry_run_result else None,
            approved=event.approved,
            execution_result=json.dumps(event.execution_result) if event.execution_result else None,
            error=event.error,
        )
        session.add(db_event)
        await session.flush()
        await session.refresh(db_event)
        logger.info(
            "Audit event written: id={} risk={} intent='{}'",
            db_event.id,
            db_event.risk_level,
            db_event.user_intent[:60],
        )
        return AuditEventRead.model_validate(db_event)

    async def update(
        self,
        session: AsyncSession,
        event_id: str,
        updates: dict[str, Any],
    ) -> AuditEventRead | None:
        """
        Update fields on an existing audit event (e.g. after approval).

        Args:
            session: Active AsyncSession.
            event_id: UUID of the event to update.
            updates: Dict of field name → new value.

        Returns:
            Updated AuditEventRead, or None if not found.
        """
        result = await session.execute(select(AuditEvent).where(AuditEvent.id == event_id))
        db_event = result.scalar_one_or_none()
        if db_event is None:
            return None

        for field_name, value in updates.items():
            if field_name in ("dry_run_result", "execution_result") and value is not None:
                value = json.dumps(value)
            setattr(db_event, field_name, value)

        session.add(db_event)
        await session.flush()
        await session.refresh(db_event)
        return AuditEventRead.model_validate(db_event)

    async def query(
        self,
        session: AsyncSession,
        page: int = 1,
        page_size: int = 50,
        cluster_context: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        risk_level: str | None = None,
    ) -> PaginatedAuditEvents:
        """
        Query audit events with optional filters, sorted by timestamp desc.

        Args:
            session: Active AsyncSession.
            page: 1-based page number.
            page_size: Number of items per page.
            cluster_context: Filter by cluster context name.
            from_date: Include events at or after this datetime.
            to_date: Include events at or before this datetime.
            risk_level: Filter by risk level string.

        Returns:
            PaginatedAuditEvents with items and pagination metadata.
        """
        stmt = select(AuditEvent)

        if cluster_context:
            stmt = stmt.where(AuditEvent.cluster_context == cluster_context)
        if from_date:
            stmt = stmt.where(AuditEvent.timestamp >= from_date)
        if to_date:
            stmt = stmt.where(AuditEvent.timestamp <= to_date)
        if risk_level:
            stmt = stmt.where(AuditEvent.risk_level == risk_level)

        # Count total matching rows.
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await session.execute(count_stmt)
        total = total_result.scalar_one()

        # Fetch the page.
        offset = (page - 1) * page_size
        stmt = stmt.order_by(AuditEvent.timestamp.desc()).offset(offset).limit(page_size)
        result = await session.execute(stmt)
        events = result.scalars().all()

        items = []
        for ev in events:
            read = AuditEventRead.model_validate(ev)
            # Deserialise JSON blobs.
            if ev.dry_run_result:
                try:
                    read.dry_run_result = json.loads(ev.dry_run_result)
                except (json.JSONDecodeError, TypeError):
                    pass
            if ev.execution_result:
                try:
                    read.execution_result = json.loads(ev.execution_result)
                except (json.JSONDecodeError, TypeError):
                    pass
            items.append(read)

        return PaginatedAuditEvents(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=max(1, math.ceil(total / page_size)),
        )

    async def export_csv(
        self,
        session: AsyncSession,
        cluster_context: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        risk_level: str | None = None,
    ) -> str:
        """
        Export matching audit events as a CSV string.

        Args:
            session: Active AsyncSession.
            cluster_context: Optional filter.
            from_date: Optional filter.
            to_date: Optional filter.
            risk_level: Optional filter.

        Returns:
            UTF-8 CSV string with header row and one data row per event.
        """
        # Fetch all matching events (no pagination for export).
        paged = await self.query(
            session=session,
            page=1,
            page_size=100_000,
            cluster_context=cluster_context,
            from_date=from_date,
            to_date=to_date,
            risk_level=risk_level,
        )

        fieldnames = [
            "id",
            "timestamp",
            "session_id",
            "user_intent",
            "cluster_context",
            "namespace",
            "generated_command",
            "risk_level",
            "approved",
            "error",
        ]

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for ev in paged.items:
            writer.writerow(
                {
                    "id": ev.id,
                    "timestamp": ev.timestamp.isoformat(),
                    "session_id": ev.session_id,
                    "user_intent": ev.user_intent,
                    "cluster_context": ev.cluster_context,
                    "namespace": ev.namespace,
                    "generated_command": ev.generated_command or "",
                    "risk_level": ev.risk_level,
                    "approved": "" if ev.approved is None else str(ev.approved),
                    "error": ev.error or "",
                }
            )

        return buf.getvalue()


# Module-level singleton.
audit_logger = AuditLogger()
