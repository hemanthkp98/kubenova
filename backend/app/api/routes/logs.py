"""
Pod log streaming API routes.

WS /api/ws/logs/{namespace}/{pod}/{container}

Streams pod logs line-by-line over a WebSocket connection. The connection
is closed when the pod stops or the client disconnects.
"""

from __future__ import annotations

import asyncio
import threading
from queue import Empty, Queue

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from app.config import get_settings
from app.core.k8s.client import get_k8s_clients

router = APIRouter(tags=["logs"])

_SENTINEL = object()


@router.websocket("/ws/logs/{namespace}/{pod}/{container}")
async def stream_pod_logs(
    websocket: WebSocket,
    namespace: str,
    pod: str,
    container: str,
    cluster_context: str = "default",
    tail: int = 100,
) -> None:
    """
    Stream pod logs over WebSocket.

    Opens a watch stream to the pod's log endpoint and forwards each line
    to the connected client. Reconnects automatically if the stream ends.

    Parameters (query):
        cluster_context: kubeconfig context name.
        tail: Number of historical lines to include before streaming new lines.
    """
    await websocket.accept()
    logger.info(
        "Log stream opened: {}/{}/{} ctx={}",
        namespace,
        pod,
        container,
        cluster_context,
    )

    settings = get_settings()
    clients = get_k8s_clients(context=cluster_context)
    line_queue: Queue[object] = Queue(maxsize=1000)

    def _stream_thread() -> None:
        """Run blocking log stream in a background thread."""
        try:
            stream = clients["core"].read_namespaced_pod_log(
                name=pod,
                namespace=namespace,
                container=container if container != "_" else None,
                follow=True,
                tail_lines=min(tail, settings.MAX_LOG_LINES),
                timestamps=True,
                _preload_content=False,
            )
            for line in stream:
                if isinstance(line, bytes):
                    line = line.decode("utf-8", errors="replace")
                line_queue.put(line.rstrip("\n"))
        except Exception as exc:
            line_queue.put(f"[ERROR] {exc}")
        finally:
            line_queue.put(_SENTINEL)

    thread = threading.Thread(target=_stream_thread, daemon=True)
    thread.start()

    try:
        while True:
            try:
                item = line_queue.get(timeout=0.1)
            except Empty:
                # Yield control so the event loop can process disconnect signals.
                await asyncio.sleep(0)
                continue

            if item is _SENTINEL:
                break
            await websocket.send_text(str(item))
    except WebSocketDisconnect:
        logger.info("Log stream client disconnected: {}/{}/{}", namespace, pod, container)
    except Exception as exc:
        logger.error("Log stream error: {}", exc)
        try:
            await websocket.send_text(f"[ERROR] {exc}")
        except Exception:
            pass
    finally:
        await websocket.close()
        logger.info("Log stream closed: {}/{}/{}", namespace, pod, container)
