/**
 * @file Paginated audit events table.
 */

import { useAudit } from "@/hooks/useAudit";
import { ResourceBadge } from "@/components/resources/ResourceBadge";
import { cn, formatAge, truncate } from "@/lib/utils";
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";

interface AuditTableProps {
  className?: string;
}

const RISK_BADGE_MAP: Record<string, string> = {
  LOW: "Running",
  MEDIUM: "Pending",
  HIGH: "Error",
  CRITICAL: "Failed",
};

export function AuditTable({ className }: AuditTableProps) {
  const { data, isLoading, page, setPage, totalPages } = useAudit({ pageSize: 20 });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-24 text-kn-text-muted">
        <Loader2 size={18} className="animate-spin mr-2" />
        <span className="text-sm">Loading audit log…</span>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col gap-3", className)}>
      <div className="overflow-x-auto">
        <table className="w-full text-xs" data-testid="audit-table">
          <thead>
            <tr className="border-b border-kn-border text-kn-text-muted">
              <th className="text-left pb-2 pr-4 font-medium">Time</th>
              <th className="text-left pb-2 pr-4 font-medium">Intent</th>
              <th className="text-left pb-2 pr-4 font-medium">Cluster</th>
              <th className="text-left pb-2 pr-4 font-medium">Risk</th>
              <th className="text-left pb-2 pr-4 font-medium">Approved</th>
              <th className="text-left pb-2 font-medium">Command</th>
            </tr>
          </thead>
          <tbody>
            {(data?.items ?? []).map((ev) => (
              <tr key={ev.id} className="border-b border-kn-border/50 hover:bg-kn-bg-elevated">
                <td className="py-2 pr-4 text-kn-text-muted whitespace-nowrap">
                  {formatAge(ev.timestamp)} ago
                </td>
                <td className="py-2 pr-4 text-kn-text-primary max-w-[200px]">
                  {truncate(ev.user_intent, 60)}
                </td>
                <td className="py-2 pr-4 text-kn-text-muted font-mono">{ev.cluster_context}</td>
                <td className="py-2 pr-4">
                  <ResourceBadge status={RISK_BADGE_MAP[ev.risk_level] ?? "Unknown"} />
                </td>
                <td className="py-2 pr-4">
                  {ev.approved === null ? (
                    <span className="text-kn-text-muted">—</span>
                  ) : ev.approved ? (
                    <span className="text-kn-success">✓</span>
                  ) : (
                    <span className="text-kn-danger">✗</span>
                  )}
                </td>
                <td className="py-2 font-mono text-kn-text-muted max-w-[200px] truncate">
                  {ev.generated_command ? truncate(ev.generated_command, 50) : "—"}
                </td>
              </tr>
            ))}
            {(data?.items ?? []).length === 0 && (
              <tr>
                <td colSpan={6} className="py-8 text-center text-kn-text-muted">
                  No audit events yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {(data?.total_pages ?? 1) > 1 && (
        <div className="flex items-center justify-between text-xs text-kn-text-muted">
          <span>Page {page} of {totalPages} ({data?.total ?? 0} events)</span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="p-1 disabled:opacity-40"
            >
              <ChevronLeft size={14} />
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="p-1 disabled:opacity-40"
            >
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
