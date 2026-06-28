"""
Chat API routes.

Provides:
  POST /api/chat          — single-turn request/response
  WS   /api/ws/chat       — streaming WebSocket chat
  POST /api/chat/approve  — deferred command approval gate
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from langchain_core.messages import AIMessage, HumanMessage
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_audit_logger, get_db
from app.core.agents.graph import compiled_graph
from app.core.agents.state import KubeNovaState
from app.core.audit.logger import AuditLogger
from app.core.audit.models import AuditEventCreate
from app.models.chat import (
    ApprovalRequest,
    ApprovalResponse,
    ChatRequest,
    ChatResponse,
    StreamChunk,
    WSIncomingMessage,
)

router = APIRouter(prefix="/chat", tags=["chat"])


def _extract_final_text(messages: list[Any]) -> str:
    """Extract the text content of the last AIMessage in a message list."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            return str(msg.content)
    return ""


def _extract_command_preview(state: KubeNovaState) -> dict | None:
    """Return command_preview dict from state, or None."""
    return state.get("command_preview")


@router.post("", response_model=ChatResponse)
async def single_turn_chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    audit: AuditLogger = Depends(get_audit_logger),
) -> ChatResponse:
    """
    Single-turn chat endpoint.

    Runs the full LangGraph agent synchronously and returns when done.
    Suitable for simple clients; prefer the WebSocket endpoint for streaming UI.
    """
    audit_create = AuditEventCreate(
        session_id=request.session_id,
        user_intent=request.message,
        cluster_context=request.cluster_context,
        namespace=request.namespace,
        risk_level="LOW",
    )
    audit_event = await audit.write(db, audit_create)

    initial_state: KubeNovaState = {
        "messages": [HumanMessage(content=request.message)],
        "cluster_context": request.cluster_context,
        "namespace": request.namespace,
        "user_intent": request.message,
        "risk_level": "LOW",
        "command_preview": None,
        "dry_run_result": None,
        "user_approved": False,
        "incident_mode": False,
        "incident_findings": [],
        "error": None,
        "audit_event_id": audit_event.id,
        "session_id": request.session_id,
        "generated_command": None,
    }

    try:
        final_state: KubeNovaState = await compiled_graph.ainvoke(initial_state)
    except Exception as exc:
        logger.error("Agent error for session {}: {}", request.session_id, exc)
        await audit.update(db, audit_event.id, {"error": str(exc)})
        raise

    response_text = _extract_final_text(final_state.get("messages", []))
    command_preview = _extract_command_preview(final_state)

    await audit.update(
        db,
        audit_event.id,
        {
            "risk_level": final_state.get("risk_level", "LOW"),
            "generated_command": final_state.get("generated_command"),
        },
    )

    return ChatResponse(
        response=response_text,
        command_preview=None,  # CommandPreview model validation from dict if present
        audit_event_id=audit_event.id,
    )


@router.post("/approve", response_model=ApprovalResponse)
async def approve_command(
    request: ApprovalRequest,
    db: AsyncSession = Depends(get_db),
    audit: AuditLogger = Depends(get_audit_logger),
) -> ApprovalResponse:
    """
    Deferred approval endpoint for HIGH-risk commands.

    The frontend calls this after the user clicks Approve or Cancel in the
    CommandPreview modal. The audit log is updated with the decision.
    """
    status = "accepted" if request.approved else "rejected"
    await audit.update(
        db,
        request.audit_event_id,
        {"approved": request.approved},
    )
    logger.info(
        "Command {}: session={} audit_event={}",
        status,
        request.session_id,
        request.audit_event_id,
    )
    return ApprovalResponse(status=status)


@router.websocket("/ws/chat")
async def websocket_chat(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
    audit: AuditLogger = Depends(get_audit_logger),
) -> None:
    """
    Streaming WebSocket chat endpoint.

    Protocol:
    1. Client sends: {"type": "chat", "message": "...", "cluster_context": "...", ...}
    2. Server streams: {"type": "token", "content": "..."}
    3. If command preview: {"type": "command_preview", "content": {...}}
       Then waits for: {"type": "approval", "approved": true/false, ...}
    4. Server sends: {"type": "done", "content": ""}
    5. On error: {"type": "error", "content": "message"}
    """
    await websocket.accept()
    logger.info("WebSocket chat connection opened.")

    try:
        while True:
            try:
                raw = await websocket.receive_text()
                msg = WSIncomingMessage.model_validate_json(raw)
            except WebSocketDisconnect:
                break
            except Exception as exc:
                await websocket.send_text(
                    StreamChunk(type="error", content=str(exc)).model_dump_json()
                )
                continue

            if msg.type == "chat":
                await _handle_chat_message(websocket, db, audit, msg)
            elif msg.type == "approval":
                # Approval handled by the dedicated REST endpoint; acknowledge.
                await websocket.send_text(
                    StreamChunk(type="done", content="approval_received").model_dump_json()
                )

    except WebSocketDisconnect:
        logger.info("WebSocket chat connection closed.")
    except Exception as exc:
        logger.error("WebSocket error: {}", exc)
        try:
            await websocket.send_text(
                StreamChunk(type="error", content=str(exc)).model_dump_json()
            )
        except Exception:
            pass


async def _handle_chat_message(
    websocket: WebSocket,
    db: AsyncSession,
    audit: AuditLogger,
    msg: WSIncomingMessage,
) -> None:
    """Process a single chat message received over the WebSocket."""
    session_id = msg.session_id or str(uuid.uuid4())
    cluster_context = msg.cluster_context or ""
    namespace = msg.namespace or "default"
    user_message = msg.message or ""

    audit_create = AuditEventCreate(
        session_id=session_id,
        user_intent=user_message,
        cluster_context=cluster_context,
        namespace=namespace,
    )
    audit_event = await audit.write(db, audit_create)

    initial_state: KubeNovaState = {
        "messages": [HumanMessage(content=user_message)],
        "cluster_context": cluster_context,
        "namespace": namespace,
        "user_intent": user_message,
        "risk_level": "LOW",
        "command_preview": None,
        "dry_run_result": None,
        "user_approved": False,
        "incident_mode": "incident" in user_message.lower(),
        "incident_findings": [],
        "error": None,
        "audit_event_id": audit_event.id,
        "session_id": session_id,
        "generated_command": None,
    }

    try:
        async for chunk in compiled_graph.astream(initial_state, stream_mode="updates"):
            for node_name, node_output in chunk.items():
                # Stream token content from executor messages.
                if node_name == "executor":
                    messages = node_output.get("messages", [])
                    for message in messages:
                        if isinstance(message, AIMessage) and message.content:
                            content = str(message.content)
                            # Stream in chunks of ~50 chars to simulate token streaming.
                            for i in range(0, len(content), 50):
                                token_chunk = content[i : i + 50]
                                await websocket.send_text(
                                    StreamChunk(
                                        type="token", content=token_chunk
                                    ).model_dump_json()
                                )

                # Surface command preview from state.
                if node_name in ("safety_gate", "human_review"):
                    cp = node_output.get("command_preview")
                    if cp:
                        await websocket.send_text(
                            StreamChunk(
                                type="command_preview",
                                content=cp if isinstance(cp, dict) else cp,
                            ).model_dump_json()
                        )

        await websocket.send_text(
            StreamChunk(type="done", content="").model_dump_json()
        )

    except Exception as exc:
        logger.error("Agent stream error: {}", exc)
        await audit.update(db, audit_event.id, {"error": str(exc)})
        await websocket.send_text(
            StreamChunk(type="error", content=str(exc)).model_dump_json()
        )
