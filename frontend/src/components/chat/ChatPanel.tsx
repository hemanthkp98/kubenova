/**
 * @file Main chat area component.
 *
 * Manages the message list, auto-scroll to the latest message,
 * streaming indicator, and command preview modal lifecycle.
 */

import { useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { CommandPreview } from "./CommandPreview";
import { StreamingIndicator } from "./StreamingIndicator";
import { IncidentModePanel } from "./IncidentModePanel";
import { useChatWebSocket } from "@/hooks/useChatWebSocket";
import { useClusterStore } from "@/store/clusterStore";
import { generateId } from "@/lib/utils";
import { useChatStore } from "@/store/chatStore";
import { chatApi } from "@/lib/api";
import { cn } from "@/lib/utils";

const PROVIDER_COLORS: Record<string, string> = {
  anthropic: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  openai:    "bg-blue-500/15 text-blue-400 border-blue-500/30",
  ollama:    "bg-purple-500/15 text-purple-400 border-purple-500/30",
};

interface ChatPanelProps {
  sessionId?: string;
  className?: string;
}

export function ChatPanel({ sessionId, className }: ChatPanelProps) {
  const sid = sessionId ?? generateId();
  const { activeCluster, activeNamespace } = useClusterStore();
  const { incidentMode, setIncidentMode } = useChatStore();

  const {
    messages,
    streamingContent,
    commandPreview,
    isStreaming,
    isConnected,
    sendMessage,
    clearContext,
    approveCommand,
  } = useChatWebSocket(sid);

  const { data: llmInfo } = useQuery({
    queryKey: ["llm-info"],
    queryFn: chatApi.getLLMInfo,
    staleTime: Infinity,
  });

  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll when messages or streaming content changes.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  const handleSend = (text: string) => {
    if (!activeCluster) {
      alert("Please select a cluster first.");
      return;
    }
    sendMessage({
      message: text,
      cluster_context: activeCluster,
      namespace: activeNamespace,
      session_id: sid,
    });
  };

  // The most recently created audit event id is embedded in the last assistant message
  // or the command preview. For simplicity we track a placeholder here.
  const pendingAuditId = commandPreview ? "pending" : null;

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Chat header — LLM badge + clear context */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-kn-border bg-kn-bg-surface">
        {llmInfo ? (
          <span
            className={cn(
              "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-mono border",
              PROVIDER_COLORS[llmInfo.provider] ?? "bg-kn-bg-elevated text-kn-text-muted border-kn-border"
            )}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70" />
            {llmInfo.model}
          </span>
        ) : (
          <span />
        )}

        <button
          onClick={clearContext}
          disabled={messages.length === 0 && !streamingContent}
          title="Clear conversation context"
          className={cn(
            "flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs transition-colors",
            "border border-kn-border text-kn-text-muted",
            "hover:text-kn-danger hover:border-kn-danger/40 hover:bg-kn-danger/5",
            "disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:text-kn-text-muted disabled:hover:border-kn-border disabled:hover:bg-transparent"
          )}
        >
          <Trash2 size={12} />
          Clear context
        </button>
      </div>

      {/* Incident mode banner */}
      {incidentMode && (
        <div className="px-4 pt-3">
          <IncidentModePanel
            findings={[]}
            onClose={() => setIncidentMode(false)}
          />
        </div>
      )}

      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-1">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-3">
              <div className="text-4xl">⎈</div>
              <p className="text-kn-text-primary font-semibold">KubeNova</p>
              <p className="text-kn-text-muted text-sm">
                Talk to your cluster. See it live. Fix it fast.
              </p>
              {!activeCluster && (
                <p className="text-kn-warning text-xs">
                  Select a cluster from the top bar to get started.
                </p>
              )}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {/* Streaming partial message */}
        {streamingContent && (
          <div className="flex gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-kn-purple/20 text-kn-purple flex items-center justify-center flex-shrink-0">
              <span className="text-xs">AI</span>
            </div>
            <div className="max-w-[75%] rounded-lg px-4 py-3 bg-kn-bg-surface border-l-2 border-kn-purple">
              <p className="whitespace-pre-wrap font-mono text-xs leading-5 text-kn-text-primary">
                {streamingContent}
              </p>
            </div>
          </div>
        )}

        {isStreaming && !streamingContent && <StreamingIndicator className="ml-11" />}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <ChatInput
        onSend={handleSend}
        disabled={isStreaming || !isConnected}
        placeholder={
          !activeCluster
            ? "Select a cluster first…"
            : isStreaming
            ? "AI is responding…"
            : "Ask about your cluster…"
        }
      />

      {/* Command preview modal */}
      {commandPreview && (
        <CommandPreview
          preview={commandPreview}
          auditEventId={pendingAuditId ?? "unknown"}
          onApprove={(id, yaml) => void approveCommand(id, true, yaml)}
          onCancel={(id) => void approveCommand(id, false)}
        />
      )}
    </div>
  );
}
