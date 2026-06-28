/**
 * @file Log streaming WebSocket hook.
 *
 * Connects to WS /api/ws/logs/{namespace}/{pod}/{container} and
 * accumulates log lines in a state array, trimming to MAX_LINES.
 */

import { useCallback, useRef, useState, useEffect } from "react";
import { logStreamUrl } from "@/lib/websocket";

const MAX_LINES = 500;

interface UseLogWebSocketReturn {
  lines: string[];
  isConnected: boolean;
  isStreaming: boolean;
  clear: () => void;
}

export function useLogWebSocket(
  namespace: string,
  pod: string,
  container: string,
  clusterContext: string,
  tail = 100,
  enabled = true
): UseLogWebSocketReturn {
  const [lines, setLines] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const clear = useCallback(() => setLines([]), []);

  useEffect(() => {
    if (!enabled || !namespace || !pod || !clusterContext) return;

    const url = logStreamUrl(namespace, pod, container || "_", clusterContext, tail);
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setIsStreaming(true);
    };

    ws.onmessage = (event: MessageEvent<string>) => {
      setLines((prev) => {
        const next = [...prev, event.data];
        return next.length > MAX_LINES ? next.slice(next.length - MAX_LINES) : next;
      });
    };

    ws.onerror = () => {
      setIsConnected(false);
      setIsStreaming(false);
    };

    ws.onclose = () => {
      setIsConnected(false);
      setIsStreaming(false);
    };

    return () => {
      ws.close(1000, "component unmounted");
    };
  }, [namespace, pod, container, clusterContext, tail, enabled]);

  return { lines, isConnected, isStreaming, clear };
}
