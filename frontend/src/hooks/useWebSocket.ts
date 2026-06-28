/**
 * @file Generic WebSocket hook with automatic reconnection and message queuing.
 *
 * Manages connection lifecycle, reconnects with exponential back-off on
 * unexpected close, and queues outbound messages while the socket is
 * disconnected.
 */

import { useCallback, useEffect, useRef, useState } from "react";

interface UseWebSocketOptions {
  /** Maximum reconnect attempts before giving up. Default: 5. */
  maxRetries?: number;
  /** Initial reconnect delay in ms. Doubles each retry. Default: 1000. */
  retryDelay?: number;
  onMessage?: (data: string) => void;
  onOpen?: () => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
}

interface UseWebSocketReturn {
  sendMessage: (data: string) => void;
  isConnected: boolean;
  reconnect: () => void;
}

export function useWebSocket(
  url: string | null,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn {
  const { maxRetries = 5, retryDelay = 1000, onMessage, onOpen, onClose, onError } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef(0);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const messageQueueRef = useRef<string[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  // Stable refs to avoid stale closures in event handlers.
  const onMessageRef = useRef(onMessage);
  const onOpenRef = useRef(onOpen);
  const onCloseRef = useRef(onClose);
  const onErrorRef = useRef(onError);
  useEffect(() => { onMessageRef.current = onMessage; }, [onMessage]);
  useEffect(() => { onOpenRef.current = onOpen; }, [onOpen]);
  useEffect(() => { onCloseRef.current = onClose; }, [onClose]);
  useEffect(() => { onErrorRef.current = onError; }, [onError]);

  const connect = useCallback(() => {
    if (!url) return;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      retryCountRef.current = 0;
      // Flush queued messages.
      while (messageQueueRef.current.length > 0) {
        const queued = messageQueueRef.current.shift();
        if (queued) ws.send(queued);
      }
      onOpenRef.current?.();
    };

    ws.onmessage = (event: MessageEvent<string>) => {
      onMessageRef.current?.(event.data);
    };

    ws.onerror = (event: Event) => {
      onErrorRef.current?.(event);
    };

    ws.onclose = (event: CloseEvent) => {
      setIsConnected(false);
      onCloseRef.current?.(event);

      // Reconnect unless the close was intentional (code 1000) or max retries hit.
      if (event.code !== 1000 && retryCountRef.current < maxRetries) {
        const delay = retryDelay * Math.pow(2, retryCountRef.current);
        retryCountRef.current += 1;
        retryTimerRef.current = setTimeout(connect, delay);
      }
    };
  }, [url, maxRetries, retryDelay]);

  useEffect(() => {
    connect();
    return () => {
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
      wsRef.current?.close(1000, "component unmounted");
    };
  }, [connect]);

  const sendMessage = useCallback((data: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
    } else {
      // Queue for delivery once reconnected.
      messageQueueRef.current.push(data);
    }
  }, []);

  const reconnect = useCallback(() => {
    if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
    wsRef.current?.close(1000, "manual reconnect");
    retryCountRef.current = 0;
    connect();
  }, [connect]);

  return { sendMessage, isConnected, reconnect };
}
