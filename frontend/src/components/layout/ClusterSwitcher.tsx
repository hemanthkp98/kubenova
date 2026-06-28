/**
 * @file Cluster context switcher dropdown in the top navigation bar.
 */

import { useCluster } from "@/hooks/useCluster";
import { cn } from "@/lib/utils";
import { ChevronDown, Server, Loader2 } from "lucide-react";
import { useState, useRef, useEffect } from "react";

interface ClusterSwitcherProps {
  className?: string;
}

export function ClusterSwitcher({ className }: ClusterSwitcherProps) {
  const { activeCluster, availableContexts, setActiveCluster, isLoading } = useCluster();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-kn-text-muted text-xs">
        <Loader2 size={12} className="animate-spin" />
        Loading clusters…
      </div>
    );
  }

  return (
    <div ref={ref} className={cn("relative", className)}>
      <button
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "flex items-center gap-2 px-3 py-1.5 rounded-md text-xs",
          "bg-kn-bg-elevated border border-kn-border text-kn-text-primary",
          "hover:border-kn-accent/50 transition-colors"
        )}
        aria-expanded={open}
        aria-haspopup="listbox"
      >
        <Server size={12} className="text-kn-accent" />
        <span className="max-w-[140px] truncate font-mono">
          {activeCluster || "Select cluster"}
        </span>
        <ChevronDown size={12} className={cn("transition-transform", open && "rotate-180")} />
      </button>

      {open && (
        <div
          className="absolute top-full left-0 mt-1 w-56 bg-kn-bg-elevated border border-kn-border rounded-md shadow-xl z-50 py-1"
          role="listbox"
        >
          {availableContexts.length === 0 ? (
            <div className="px-3 py-2 text-xs text-kn-text-muted">No contexts found</div>
          ) : (
            availableContexts.map((ctx) => (
              <button
                key={ctx.name}
                role="option"
                aria-selected={ctx.name === activeCluster}
                onClick={() => {
                  void setActiveCluster(ctx.name);
                  setOpen(false);
                }}
                className={cn(
                  "w-full text-left px-3 py-2 text-xs font-mono flex items-center gap-2",
                  "hover:bg-kn-bg-base transition-colors",
                  ctx.name === activeCluster && "text-kn-accent"
                )}
              >
                <span className={cn("w-1.5 h-1.5 rounded-full flex-shrink-0", ctx.name === activeCluster ? "bg-kn-success" : "bg-kn-border")} />
                <span className="truncate">{ctx.name}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
