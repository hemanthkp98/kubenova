"""
Unit tests for app.core.audit.logger.AuditLogger.

Uses the in-memory SQLite db_session fixture from conftest.py.
No real database file is created.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest
import pytest_asyncio

from app.core.audit.logger import AuditLogger
from app.core.audit.models import AuditEventCreate


@pytest_asyncio.fixture
async def audit_logger() -> AuditLogger:
    """Return an AuditLogger instance."""
    return AuditLogger()


class TestAuditLoggerWrite:
    """Tests for AuditLogger.write()."""

    async def test_write_and_read_back(self, audit_logger: AuditLogger, db_session) -> None:
        """Write an event and verify all fields are persisted correctly."""
        create = AuditEventCreate(
            session_id="sess-001",
            user_intent="show me all pods",
            cluster_context="minikube",
            namespace="default",
            risk_level="LOW",
        )
        event = await audit_logger.write(db_session, create)

        assert event.id is not None
        assert event.session_id == "sess-001"
        assert event.user_intent == "show me all pods"
        assert event.cluster_context == "minikube"
        assert event.risk_level == "LOW"
        assert event.approved is None

    async def test_write_returns_generated_id(self, audit_logger: AuditLogger, db_session) -> None:
        """Written event has a non-empty UUID id."""
        create = AuditEventCreate(
            session_id="sess-002",
            user_intent="delete pod",
            cluster_context="prod",
            namespace="kube-system",
            risk_level="HIGH",
        )
        event = await audit_logger.write(db_session, create)
        assert len(event.id) == 36  # UUID format

    async def test_write_multiple_events(self, audit_logger: AuditLogger, db_session) -> None:
        """Multiple events can be written and each gets a unique id."""
        ids = set()
        for i in range(5):
            create = AuditEventCreate(
                session_id=f"sess-{i}",
                user_intent=f"intent-{i}",
                cluster_context="minikube",
                namespace="default",
            )
            ev = await audit_logger.write(db_session, create)
            ids.add(ev.id)
        assert len(ids) == 5


class TestAuditLoggerQuery:
    """Tests for AuditLogger.query()."""

    async def test_query_returns_all_events(self, audit_logger: AuditLogger, db_session) -> None:
        """query() returns all events when no filters are applied."""
        for i in range(3):
            await audit_logger.write(
                db_session,
                AuditEventCreate(
                    session_id=f"s{i}", user_intent=f"i{i}", cluster_context="ctx", namespace="ns"
                ),
            )
        result = await audit_logger.query(db_session)
        assert result.total == 3

    async def test_filter_by_risk_level(self, audit_logger: AuditLogger, db_session) -> None:
        """Query by risk_level returns only matching events."""
        await audit_logger.write(
            db_session,
            AuditEventCreate(session_id="s1", user_intent="i1", cluster_context="c", namespace="n", risk_level="HIGH"),
        )
        await audit_logger.write(
            db_session,
            AuditEventCreate(session_id="s2", user_intent="i2", cluster_context="c", namespace="n", risk_level="LOW"),
        )
        result = await audit_logger.query(db_session, risk_level="HIGH")
        assert result.total == 1
        assert result.items[0].risk_level == "HIGH"

    async def test_filter_by_date_range_excludes_old(self, audit_logger: AuditLogger, db_session) -> None:
        """Events outside the date range are excluded."""
        await audit_logger.write(
            db_session,
            AuditEventCreate(session_id="s1", user_intent="old", cluster_context="c", namespace="n"),
        )
        future = datetime.now(tz=timezone.utc) + timedelta(hours=1)
        result = await audit_logger.query(db_session, from_date=future)
        assert result.total == 0

    async def test_pagination_page_size(self, audit_logger: AuditLogger, db_session) -> None:
        """page_size limits the number of returned items."""
        for i in range(10):
            await audit_logger.write(
                db_session,
                AuditEventCreate(session_id=f"s{i}", user_intent=f"i{i}", cluster_context="c", namespace="n"),
            )
        result = await audit_logger.query(db_session, page=1, page_size=3)
        assert len(result.items) == 3
        assert result.total == 10

    async def test_filter_by_cluster_context(self, audit_logger: AuditLogger, db_session) -> None:
        """Events from a different cluster are excluded."""
        await audit_logger.write(
            db_session,
            AuditEventCreate(session_id="s1", user_intent="i1", cluster_context="cluster-a", namespace="n"),
        )
        await audit_logger.write(
            db_session,
            AuditEventCreate(session_id="s2", user_intent="i2", cluster_context="cluster-b", namespace="n"),
        )
        result = await audit_logger.query(db_session, cluster_context="cluster-a")
        assert result.total == 1
        assert result.items[0].cluster_context == "cluster-a"


class TestAuditLoggerCSVExport:
    """Tests for AuditLogger.export_csv()."""

    async def test_csv_has_header_row(self, audit_logger: AuditLogger, db_session) -> None:
        """Export includes the CSV header row."""
        csv_str = await audit_logger.export_csv(db_session)
        assert csv_str.startswith("id,")

    async def test_csv_with_data_has_correct_row_count(self, audit_logger: AuditLogger, db_session) -> None:
        """Export has one data row per event plus the header."""
        for i in range(3):
            await audit_logger.write(
                db_session,
                AuditEventCreate(session_id=f"s{i}", user_intent=f"i{i}", cluster_context="c", namespace="n"),
            )
        csv_str = await audit_logger.export_csv(db_session)
        lines = [line for line in csv_str.splitlines() if line.strip()]
        assert len(lines) == 4  # 1 header + 3 data rows

    async def test_csv_with_no_data_has_only_header(self, audit_logger: AuditLogger, db_session) -> None:
        """Export with no events returns only the header row."""
        csv_str = await audit_logger.export_csv(db_session)
        lines = [line for line in csv_str.splitlines() if line.strip()]
        assert len(lines) == 1  # header only

    async def test_csv_filtered_by_risk_level(self, audit_logger: AuditLogger, db_session) -> None:
        """CSV export respects risk_level filter."""
        await audit_logger.write(
            db_session,
            AuditEventCreate(session_id="s1", user_intent="i1", cluster_context="c", namespace="n", risk_level="CRITICAL"),
        )
        await audit_logger.write(
            db_session,
            AuditEventCreate(session_id="s2", user_intent="i2", cluster_context="c", namespace="n", risk_level="LOW"),
        )
        csv_str = await audit_logger.export_csv(db_session, risk_level="CRITICAL")
        lines = [line for line in csv_str.splitlines() if line.strip()]
        assert len(lines) == 2  # header + 1 data
