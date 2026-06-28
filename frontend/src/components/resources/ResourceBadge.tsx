/**
 * @file Reusable status badge for Kubernetes resource states.
 *
 * Colour mapping covers the most common pod, node, and deployment statuses.
 * Unknown statuses fall back to the muted style.
 */

import { cn } from "@/lib/utils";

interface ResourceBadgeProps {
  status: string;
  className?: string;
}

const STATUS_STYLES: Record<string, string> = {
  Running: "bg-kn-success/15 text-kn-success border-kn-success/30",
  Succeeded: "bg-kn-success/15 text-kn-success border-kn-success/30",
  Ready: "bg-kn-success/15 text-kn-success border-kn-success/30",
  Pending: "bg-kn-warning/15 text-kn-warning border-kn-warning/30",
  ContainerCreating: "bg-kn-warning/15 text-kn-warning border-kn-warning/30",
  Terminating: "bg-kn-warning/15 text-kn-warning border-kn-warning/30",
  Failed: "bg-kn-danger/15 text-kn-danger border-kn-danger/30",
  CrashLoopBackOff: "bg-kn-danger/15 text-kn-danger border-kn-danger/30",
  Error: "bg-kn-danger/15 text-kn-danger border-kn-danger/30",
  OOMKilled: "bg-kn-danger/15 text-kn-danger border-kn-danger/30",
  NotReady: "bg-kn-danger/15 text-kn-danger border-kn-danger/30",
  Unknown: "bg-kn-text-muted/15 text-kn-text-muted border-kn-text-muted/30",
};

export function ResourceBadge({ status, className }: ResourceBadgeProps) {
  const style = STATUS_STYLES[status] ?? "bg-kn-text-muted/15 text-kn-text-muted border-kn-text-muted/30";
  return (
    <span
      className={cn(
        "inline-flex items-center px-1.5 py-0.5 rounded border text-[10px] font-medium uppercase tracking-wide",
        style,
        className
      )}
      data-testid="resource-badge"
    >
      {status}
    </span>
  );
}
