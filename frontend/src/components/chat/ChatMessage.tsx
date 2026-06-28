/**
 * @file Single chat message bubble component.
 *
 * Renders three visually distinct styles:
 * - user: right-aligned, no border
 * - assistant: left border in kn-purple, radial gradient background
 * - system: muted center-aligned notice (info/error/cancellation messages)
 *
 * The tri-party visual language (user / AI / system) lets operators scan
 * the conversation at a glance without reading every line.
 */

import { cn, formatAge } from "@/lib/utils";
import type { ChatMessage as ChatMessageType } from "@/types/chat";
import { Bot, User, Info } from "lucide-react";

interface ChatMessageProps {
  message: ChatMessageType;
  className?: string;
}

export function ChatMessage({ message, className }: ChatMessageProps) {
  const isUser = message.role === "user";
  const isAssistant = message.role === "assistant";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className={cn("flex justify-center my-2", className)}>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-kn-bg-elevated border border-kn-border text-kn-text-muted text-xs">
          <Info size={12} />
          <span>{message.content}</span>
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex gap-3 mb-4",
        isUser ? "flex-row-reverse" : "flex-row",
        className
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
          isUser ? "bg-kn-accent/20 text-kn-accent" : "bg-kn-purple/20 text-kn-purple"
        )}
      >
        {isUser ? <User size={14} /> : <Bot size={14} />}
      </div>

      {/* Bubble */}
      <div
        className={cn(
          "max-w-[75%] rounded-lg px-4 py-3 text-sm leading-relaxed",
          isUser && "bg-kn-bg-elevated text-kn-text-primary",
          isAssistant && [
            "bg-kn-bg-surface text-kn-text-primary",
            "border-l-2 border-kn-purple",
            "relative",
            // Subtle radial gradient on assistant messages.
            "before:absolute before:inset-0 before:rounded-lg",
            "before:bg-[radial-gradient(ellipse_at_left,rgba(188,140,255,0.06)_0%,transparent_70%)]",
            "before:pointer-events-none",
          ]
        )}
      >
        {/* Prose — preserve whitespace for code/terminal output */}
        <p className="whitespace-pre-wrap font-mono text-xs leading-5 text-kn-text-primary">
          {message.content}
        </p>
        <time className="block mt-1.5 text-kn-text-muted text-[10px]">
          {formatAge(message.timestamp)} ago
        </time>
      </div>
    </div>
  );
}
