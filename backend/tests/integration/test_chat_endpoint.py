"""
Integration tests for the POST /api/chat endpoint.

The LangGraph agent is mocked to avoid real LLM calls.
The database uses the in-memory SQLite fixture.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.core.agents.state import KubeNovaState
from langchain_core.messages import AIMessage


def _make_final_state(response: str = "Here are the pods.") -> KubeNovaState:
    """Build a minimal completed agent state."""
    return {
        "messages": [AIMessage(content=response)],
        "cluster_context": "minikube",
        "namespace": "default",
        "user_intent": "list pods",
        "risk_level": "LOW",
        "command_preview": None,
        "dry_run_result": None,
        "user_approved": False,
        "incident_mode": False,
        "incident_findings": [],
        "error": None,
        "audit_event_id": "test-uuid",
        "session_id": "sess-integration",
        "generated_command": None,
    }


@pytest.mark.asyncio
class TestChatEndpoint:
    """Tests for POST /api/chat."""

    async def test_basic_chat_returns_response(self, async_client) -> None:
        """POST /api/chat returns a 200 with a response string."""
        with patch(
            "app.api.routes.chat.compiled_graph.ainvoke",
            new_callable=AsyncMock,
            return_value=_make_final_state("Found 3 pods in default namespace."),
        ):
            response = await async_client.post(
                "/api/chat",
                json={
                    "message": "list pods",
                    "cluster_context": "minikube",
                    "namespace": "default",
                    "session_id": "sess-integration",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "audit_event_id" in data

    async def test_chat_creates_audit_event(self, async_client, db_session) -> None:
        """POST /api/chat writes an audit event to the database."""
        from sqlalchemy import select
        from app.core.audit.models import AuditEvent

        with patch(
            "app.api.routes.chat.compiled_graph.ainvoke",
            new_callable=AsyncMock,
            return_value=_make_final_state(),
        ):
            await async_client.post(
                "/api/chat",
                json={
                    "message": "get deployments",
                    "cluster_context": "prod",
                    "namespace": "kube-system",
                    "session_id": "sess-audit-test",
                },
            )

        result = await db_session.execute(
            select(AuditEvent).where(AuditEvent.session_id == "sess-audit-test")
        )
        events = result.scalars().all()
        assert len(events) == 1
        assert events[0].user_intent == "get deployments"

    async def test_chat_missing_fields_returns_422(self, async_client) -> None:
        """POST /api/chat with missing required fields returns 422."""
        response = await async_client.post("/api/chat", json={"message": "hi"})
        assert response.status_code == 422

    async def test_approve_command_accepted(self, async_client) -> None:
        """POST /api/chat/approve with approved=true returns status='accepted'."""
        # We can't easily get the session here, so just test the endpoint directly.
        response = await async_client.post(
            "/api/chat/approve",
            json={
                "session_id": "sess-approve",
                "audit_event_id": "fake-uuid-does-not-exist",
                "approved": True,
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "accepted"

    async def test_approve_command_rejected(self, async_client) -> None:
        """POST /api/chat/approve with approved=false returns status='rejected'."""
        response = await async_client.post(
            "/api/chat/approve",
            json={
                "session_id": "sess-reject",
                "audit_event_id": "fake-uuid",
                "approved": False,
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "rejected"
