/**
 * @file TypeScript interfaces for chat messages, streaming chunks, and command previews.
 */

export type MessageRole = "user" | "assistant" | "system";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  /** Present when this message contains a command that was previewed. */
  commandPreview?: CommandPreview;
}

export interface CommandPreview {
  kubectl_command: string;
  manifest_yaml: string | null;
  diff: string;
  warnings: string[];
  resource_name: string;
  resource_kind: string;
  risk_level: RiskLevel;
  is_safe: boolean;
}

export type StreamChunkType = "token" | "command_preview" | "done" | "error";

export interface StreamChunk {
  type: StreamChunkType;
  content: string | CommandPreview;
}

export interface ChatRequest {
  message: string;
  cluster_context: string;
  namespace: string;
  session_id: string;
}

export interface ChatResponse {
  response: string;
  command_preview: CommandPreview | null;
  audit_event_id: string;
}

export interface ApprovalRequest {
  session_id: string;
  audit_event_id: string;
  approved: boolean;
}

export interface ApprovalResponse {
  approved: boolean;
  session_id: string;
}

export interface WSIncomingMessage {
  type: "chat" | "approval";
  message?: string;
  cluster_context?: string;
  namespace?: string;
  session_id?: string;
  approved?: boolean;
  audit_event_id?: string;
}
