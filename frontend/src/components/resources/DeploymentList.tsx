/**
 * @file Deployments table with replica ratio progress bar.
 */

import { useDeployments } from "@/hooks/useResources";
import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

interface DeploymentListProps {
  className?: string;
}

function ReplicaBar({ ready, desired }: { ready: number; desired: number }) {
  const pct = desired === 0 ? 100 : Math.round((ready / desired) * 100);
  const color = pct === 100 ? "bg-kn-success" : pct >= 50 ? "bg-kn-warning" : "bg-kn-danger";
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 bg-kn-bg-elevated rounded-full overflow-hidden">
        <div className={cn("h-full rounded-full transition-all", color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-kn-text-muted text-[10px]">{ready}/{desired}</span>
    </div>
  );
}

export function DeploymentList({ className }: DeploymentListProps) {
  const { data: deployments, isLoading, error } = useDeployments();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-24 text-kn-text-muted">
        <Loader2 size={18} className="animate-spin mr-2" />
        <span className="text-sm">Loading deployments…</span>
      </div>
    );
  }

  if (error) {
    return <div className="text-kn-danger text-xs p-3">Failed to load deployments.</div>;
  }

  return (
    <div className={cn("overflow-x-auto", className)}>
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-kn-border text-kn-text-muted">
            <th className="text-left pb-2 pr-4 font-medium">Name</th>
            <th className="text-left pb-2 pr-4 font-medium">Replicas</th>
            <th className="text-left pb-2 pr-4 font-medium">Images</th>
            <th className="text-left pb-2 font-medium">Age</th>
          </tr>
        </thead>
        <tbody>
          {(deployments ?? []).map((d) => (
            <tr
              key={`${d.namespace}/${d.name}`}
              className="border-b border-kn-border/50 hover:bg-kn-bg-elevated"
            >
              <td className="py-2 pr-4">
                <span className="text-kn-text-primary font-mono">{d.name}</span>
              </td>
              <td className="py-2 pr-4">
                <ReplicaBar ready={d.ready} desired={d.desired} />
              </td>
              <td className="py-2 pr-4 text-kn-text-muted font-mono truncate max-w-[180px]">
                {d.images[0] ?? "—"}
              </td>
              <td className="py-2 text-kn-text-muted">{d.age}</td>
            </tr>
          ))}
          {(deployments ?? []).length === 0 && (
            <tr>
              <td colSpan={4} className="py-6 text-center text-kn-text-muted">
                No deployments found.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
