"""
Integration tests for the WS /api/ws/chat WebSocket endpoint.

Uses httpx's WebSocket support to test the streaming protocol without
requiring a real LLM or Kubernetes cluster.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from app.core.agents.state import KubeNovaState


def _make_stream_chunks(text: str = "Hello from KubeNova"):
    """Yield state update dicts simulating LangGraph astream output."""
    ai_msg = AIMessage(content=text)

    async def _gen():
        yield {"executor": {"messages": [ai_msg]}}

    return _gen()


@pytest.mark.asyncio
class TestWebSocketChat:
    """Tests for WS /api/ws/chat."""

    async def test_ws_connection_accepted(self, async_client) -> None:
        """WebSocket connection is accepted without errors."""
        async with async_client.websocket_connect("/api/ws/chat") as ws:
            # Connection should be open; immediately close.
            await ws.close()

    async def test_ws_chat_receives_token_chunks(self, async_client) -> None:
        """Sending a chat message returns token chunks followed by done."""
        with patch(
            "app.api.routes.chat.compiled_graph.astream",
            return_value=_make_stream_chunks("Here are your pods."),
        ):
            async with async_client.websocket_connect("/api/ws/chat") as ws:
                await ws.send_text(json.dumps({
                    "type": "chat",
                    "message": "show pods",
                    "cluster_context": "minikube",
                    "namespace": "default",
                    "session_id": "ws-test-01",
                }))

                received_types = []
                for _ in range(10):
                    raw = await ws.receive_text()
                    chunk = json.loads(raw)
                    received_types.append(chunk["type"])
                    if chunk["type"] == "done":
                        break

        assert "done" in received_types

    async def test_ws_invalid_json_returns_error(self, async_client) -> None:
        """Sending malformed JSON returns an error chunk."""
        async with async_client.websocket_connect("/api/ws/chat") as ws:
            await ws.send_text("this is not json{{{")
            raw = await ws.receive_text()
            chunk = json.loads(raw)
            assert chunk["type"] == "error"

    async def test_ws_approval_message_acknowledged(self, async_client) -> None:
        """Sending an approval message returns a done acknowledgement."""
        async with async_client.websocket_connect("/api/ws/chat") as ws:
            await ws.send_text(json.dumps({
                "type": "approval",
                "approved": True,
                "audit_event_id": "fake-id",
                "session_id": "ws-approval",
            }))
            raw = await ws.receive_text()
            chunk = json.loads(raw)
            assert chunk["type"] == "done"
            assert "approval" in chunk["content"]
