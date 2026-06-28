/**
 * @file Services table with type and port information.
 */

import { useServices } from "@/hooks/useResources";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface ServiceListProps {
  className?: string;
}

export function ServiceList({ className }: ServiceListProps) {
  const { data: services, isLoading, error } = useServices();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-24 text-kn-text-muted">
        <Loader2 size={18} className="animate-spin mr-2" />
        <span className="text-sm">Loading services…</span>
      </div>
    );
  }

  if (error) {
    return <div className="text-kn-danger text-xs p-3">Failed to load services.</div>;
  }

  return (
    <div className={cn("overflow-x-auto", className)}>
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-kn-border text-kn-text-muted">
            <th className="text-left pb-2 pr-4 font-medium">Name</th>
            <th className="text-left pb-2 pr-4 font-medium">Type</th>
            <th className="text-left pb-2 pr-4 font-medium">Cluster IP</th>
            <th className="text-left pb-2 pr-4 font-medium">Ports</th>
            <th className="text-left pb-2 font-medium">Age</th>
          </tr>
        </thead>
        <tbody>
          {(services ?? []).map((svc) => (
            <tr
              key={`${svc.namespace}/${svc.name}`}
              className="border-b border-kn-border/50 hover:bg-kn-bg-elevated"
            >
              <td className="py-2 pr-4 font-mono text-kn-text-primary">{svc.name}</td>
              <td className="py-2 pr-4">
                <span className="text-kn-accent text-[10px] uppercase tracking-wider">{svc.type}</span>
              </td>
              <td className="py-2 pr-4 text-kn-text-muted font-mono">{svc.cluster_ip ?? "—"}</td>
              <td className="py-2 pr-4 text-kn-text-muted font-mono">
                {svc.ports.map((p) => `${p.port}/${p.protocol}`).join(", ") || "—"}
              </td>
              <td className="py-2 text-kn-text-muted">{svc.age}</td>
            </tr>
          ))}
          {(services ?? []).length === 0 && (
            <tr>
              <td colSpan={5} className="py-6 text-center text-kn-text-muted">
                No services found.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
