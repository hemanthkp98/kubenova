/**
 * @file Chat input area with send button.
 *
 * - Enter sends the message.
 * - Shift+Enter inserts a newline.
 * - An empty or whitespace-only message does nothing.
 * - The textarea auto-grows up to 6 rows.
 */

import { useRef, useState, KeyboardEvent } from "react";
import { Send } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export function ChatInput({
  onSend,
  disabled = false,
  placeholder = "Ask about your cluster…",
  className,
}: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    // Reset height.
    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    const maxHeight = 6 * 24; // 6 rows × ~24px line height
    el.style.height = `${Math.min(el.scrollHeight, maxHeight)}px`;
  };

  return (
    <div
      className={cn(
        "flex items-end gap-3 p-3 bg-kn-bg-surface border-t border-kn-border",
        className
      )}
    >
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => {
          setValue(e.target.value);
          handleInput();
        }}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        placeholder={placeholder}
        rows={1}
        className={cn(
          "flex-1 resize-none rounded-md px-3 py-2 text-sm font-mono",
          "bg-kn-bg-base border border-kn-border text-kn-text-primary",
          "placeholder:text-kn-text-muted",
          "focus:outline-none focus:ring-1 focus:ring-kn-accent",
          "disabled:opacity-50 disabled:cursor-not-allowed",
          "transition-all overflow-hidden"
        )}
        aria-label="Chat input"
        data-testid="chat-input"
      />
      <button
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        aria-label="Send message"
        className={cn(
          "flex-shrink-0 w-9 h-9 rounded-md flex items-center justify-center",
          "bg-kn-accent text-white transition-opacity",
          "hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
        )}
        data-testid="send-button"
      >
        <Send size={16} />
      </button>
    </div>
  );
}
