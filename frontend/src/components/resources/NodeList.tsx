/**
 * @file Node list with ready status and resource pressure indicators.
 */

import { useNodes } from "@/hooks/useResources";
import { ResourceBadge } from "./ResourceBadge";
import { cn } from "@/lib/utils";
import { Loader2, AlertTriangle } from "lucide-react";

interface NodeListProps {
  className?: string;
}

export function NodeList({ className }: NodeListProps) {
  const { data: nodes, isLoading, error } = useNodes();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-24 text-kn-text-muted">
        <Loader2 size={18} className="animate-spin mr-2" />
        <span className="text-sm">Loading nodes…</span>
      </div>
    );
  }

  if (error) {
    return <div className="text-kn-danger text-xs p-3">Failed to load nodes.</div>;
  }

  return (
    <div className={cn("overflow-x-auto", className)}>
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-kn-border text-kn-text-muted">
            <th className="text-left pb-2 pr-4 font-medium">Name</th>
            <th className="text-left pb-2 pr-4 font-medium">Status</th>
            <th className="text-left pb-2 pr-4 font-medium">Roles</th>
            <th className="text-left pb-2 pr-4 font-medium">Version</th>
            <th className="text-left pb-2 pr-4 font-medium">Pressure</th>
            <th className="text-left pb-2 font-medium">Age</th>
          </tr>
        </thead>
        <tbody>
          {(nodes ?? []).map((node) => {
            const pressures = node.conditions
              .filter((c) => ["MemoryPressure", "DiskPressure", "PIDPressure"].includes(c.type) && c.status === "True")
              .map((c) => c.type);

            return (
              <tr key={node.name} className="border-b border-kn-border/50 hover:bg-kn-bg-elevated">
                <td className="py-2 pr-4 font-mono text-kn-text-primary">{node.name}</td>
                <td className="py-2 pr-4">
                  <ResourceBadge status={node.status} />
                </td>
                <td className="py-2 pr-4 text-kn-text-muted">{node.roles.join(", ")}</td>
                <td className="py-2 pr-4 text-kn-text-muted font-mono">{node.version}</td>
                <td className="py-2 pr-4">
                  {pressures.length > 0 ? (
                    <span className="flex items-center gap-1 text-kn-danger text-[10px]">
                      <AlertTriangle size={10} />
                      {pressures.join(", ")}
                    </span>
                  ) : (
                    <span className="text-kn-text-muted">—</span>
                  )}
                </td>
                <td className="py-2 text-kn-text-muted">{node.age}</td>
              </tr>
            );
          })}
          {(nodes ?? []).length === 0 && (
            <tr>
              <td colSpan={6} className="py-6 text-center text-kn-text-muted">
                No nodes found.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
