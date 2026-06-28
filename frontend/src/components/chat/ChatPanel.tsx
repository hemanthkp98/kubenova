/**
 * @file Main chat area component.
 *
 * Manages the message list, auto-scroll to the latest message,
 * streaming indicator, and command preview modal lifecycle.
 */

import { useEffect, useRef } from "react";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { CommandPreview } from "./CommandPreview";
import { StreamingIndicator } from "./StreamingIndicator";
import { IncidentModePanel } from "./IncidentModePanel";
import { useChatWebSocket } from "@/hooks/useChatWebSocket";
import { useClusterStore } from "@/store/clusterStore";
import { generateId } from "@/lib/utils";
import { useChatStore } from "@/store/chatStore";
import { cn } from "@/lib/utils";

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
    approveCommand,
  } = useChatWebSocket(sid);

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
          onApprove={(id) => void approveCommand(id, true)}
          onCancel={(id) => void approveCommand(id, false)}
        />
      )}
    </div>
  );
}
