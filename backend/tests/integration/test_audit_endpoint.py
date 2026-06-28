"""
Integration tests for GET /api/audit and GET /api/audit/export.
"""

from __future__ import annotations

import pytest

from app.core.audit.models import AuditEventCreate


async def _write_events(audit, session, count: int = 3) -> None:
    """Helper to write N audit events."""
    for i in range(count):
        await audit.write(
            session,
            AuditEventCreate(
                session_id=f"s{i}",
                user_intent=f"intent {i}",
                cluster_context="minikube",
                namespace="default",
                risk_level="LOW" if i % 2 == 0 else "HIGH",
            ),
        )


@pytest.mark.asyncio
class TestAuditEndpoint:
    """Tests for GET /api/audit."""

    async def test_empty_audit_returns_zero_total(self, async_client) -> None:
        """Empty audit log returns total=0."""
        response = await async_client.get("/api/audit")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_audit_returns_events_after_write(
        self, async_client, db_session
    ) -> None:
        """After writing events, GET /api/audit returns them."""
        from app.api.deps import get_audit_logger
        audit = get_audit_logger()
        await _write_events(audit, db_session, count=5)

        response = await async_client.get("/api/audit")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5

    async def test_audit_pagination(self, async_client, db_session) -> None:
        """page_size limits the response items count."""
        from app.api.deps import get_audit_logger
        audit = get_audit_logger()
        await _write_events(audit, db_session, count=10)

        response = await async_client.get("/api/audit?page=1&page_size=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 10

    async def test_audit_filter_by_risk(self, async_client, db_session) -> None:
        """risk_level filter returns only matching events."""
        from app.api.deps import get_audit_logger
        audit = get_audit_logger()
        await _write_events(audit, db_session, count=6)

        response = await async_client.get("/api/audit?risk_level=HIGH")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["risk_level"] == "HIGH"


@pytest.mark.asyncio
class TestAuditExportEndpoint:
    """Tests for GET /api/audit/export."""

    async def test_export_returns_csv_content_type(self, async_client) -> None:
        """Export endpoint returns text/csv content type."""
        response = await async_client.get("/api/audit/export")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    async def test_export_has_header_row(self, async_client) -> None:
        """CSV export includes the header row even when empty."""
        response = await async_client.get("/api/audit/export")
        assert response.text.startswith("id,")

    async def test_export_has_attachment_disposition(self, async_client) -> None:
        """Export response has Content-Disposition: attachment."""
        response = await async_client.get("/api/audit/export")
        assert "attachment" in response.headers.get("content-disposition", "")

    async def test_export_includes_written_events(self, async_client, db_session) -> None:
        """CSV export includes events written to the database."""
        from app.api.deps import get_audit_logger
        audit = get_audit_logger()
        await _write_events(audit, db_session, count=2)

        response = await async_client.get("/api/audit/export")
        lines = [l for l in response.text.splitlines() if l.strip()]
        assert len(lines) == 3  # header + 2 rows
