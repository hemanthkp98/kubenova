/**
 * @file Animated typing indicator shown while the AI is generating a response.
 *
 * Renders three pulsing dots in kn-purple, the colour reserved for AI elements,
 * so the indicator is visually consistent with AI message bubbles.
 */

import { cn } from "@/lib/utils";

interface StreamingIndicatorProps {
  className?: string;
}

export function StreamingIndicator({ className }: StreamingIndicatorProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-1.5 px-4 py-3 rounded-lg",
        "bg-kn-bg-surface border-l-2 border-kn-purple",
        "max-w-[80px]",
        className
      )}
      aria-label="AI is typing"
      role="status"
    >
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-2 h-2 rounded-full bg-kn-purple animate-pulse-dot"
          style={{ animationDelay: `${i * 0.2}s` }}
        />
      ))}
    </div>
  );
}
