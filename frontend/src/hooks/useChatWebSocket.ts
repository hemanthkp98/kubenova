/**
 * @file Chat-specific WebSocket hook.
 *
 * Wraps useWebSocket to handle the KubeNova streaming protocol:
 * token chunks are accumulated into streamingContent and flushed to
 * messages on "done". command_preview chunks trigger the approval UI.
 */

import { useCallback } from "react";
import { useWebSocket } from "./useWebSocket";
import { useChatStore } from "@/store/chatStore";
import type { ChatMessage, CommandPreview, StreamChunk, ChatRequest } from "@/types/chat";
import { chatApi } from "@/lib/api";

const WS_URL = `${typeof window !== "undefined"
  ? (window.location.protocol === "https:" ? "wss:" : "ws:") + "//" + window.location.host
  : "ws://localhost:8000"}/api/chat/ws/chat`;

export interface UseChatWebSocketReturn {
  sendMessage: (payload: ChatRequest) => void;
  clearContext: () => void;
  messages: ChatMessage[];
  streamingContent: string;
  commandPreview: CommandPreview | null;
  isStreaming: boolean;
  isConnected: boolean;
  approveCommand: (auditEventId: string, approved: boolean) => Promise<void>;
  clearHistory: () => void;
}

export function useChatWebSocket(sessionId: string): UseChatWebSocketReturn {
  const {
    messages,
    streamingContent,
    commandPreview,
    isStreaming,
    addMessage,
    appendToken,
    flushStreaming,
    setCommandPreview,
    setIsStreaming,
    clearHistory,
  } = useChatStore();

  const handleMessage = useCallback(
    (raw: string) => {
      let chunk: StreamChunk;
      try {
        chunk = JSON.parse(raw) as StreamChunk;
      } catch {
        return;
      }

      switch (chunk.type) {
        case "token":
          setIsStreaming(true);
          appendToken(chunk.content as string);
          break;

        case "command_preview":
          setCommandPreview(chunk.content as CommandPreview);
          break;

        case "done":
          flushStreaming();
          break;

        case "error":
          flushStreaming();
          addMessage("system", `Error: ${chunk.content as string}`);
          break;
      }
    },
    [appendToken, addMessage, flushStreaming, setCommandPreview, setIsStreaming]
  );

  const { sendMessage: wsSend, isConnected } = useWebSocket(WS_URL, {
    onMessage: handleMessage,
  });

  const sendMessage = useCallback(
    (payload: ChatRequest) => {
      addMessage("user", payload.message);
      setIsStreaming(true);
      wsSend(
        JSON.stringify({
          type: "chat",
          ...payload,
        })
      );
    },
    [addMessage, setIsStreaming, wsSend]
  );

  const approveCommand = useCallback(
    async (auditEventId: string, approved: boolean) => {
      await chatApi.approveCommand({ session_id: sessionId, audit_event_id: auditEventId, approved });
      setCommandPreview(null);
      if (!approved) {
        addMessage("system", "Command cancelled by user.");
      }
    },
    [sessionId, addMessage, setCommandPreview]
  );

  const clearContext = useCallback(() => {
    clearHistory();
    wsSend(JSON.stringify({ type: "clear_context" }));
  }, [clearHistory, wsSend]);

  return {
    sendMessage,
    clearContext,
    messages,
    streamingContent,
    commandPreview,
    isStreaming,
    isConnected,
    approveCommand,
    clearHistory,
  };
}
