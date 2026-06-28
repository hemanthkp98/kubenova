/**
 * @file Pods table with status badges and log viewer trigger.
 *
 * Clicking a pod row opens the log viewer for that pod's first container.
 */

import { useState } from "react";
import { ResourceBadge } from "./ResourceBadge";
import { LogViewer } from "@/components/logs/LogViewer";
import { usePods } from "@/hooks/useResources";
import { useClusterStore } from "@/store/clusterStore";
import { cn } from "@/lib/utils";
import type { PodInfo } from "@/types/resource";
import { Loader2 } from "lucide-react";

interface PodListProps {
  className?: string;
}

export function PodList({ className }: PodListProps) {
  const { data: pods, isLoading, error } = usePods();
  const { activeCluster } = useClusterStore();
  const [selectedPod, setSelectedPod] = useState<PodInfo | null>(null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-24 text-kn-text-muted">
        <Loader2 size={18} className="animate-spin mr-2" />
        <span className="text-sm">Loading pods…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-kn-danger text-xs p-3">
        Failed to load pods: {String(error)}
      </div>
    );
  }

  return (
    <>
      <div className={cn("overflow-x-auto", className)}>
        <table className="w-full text-xs" data-testid="pod-list">
          <thead>
            <tr className="border-b border-kn-border text-kn-text-muted">
              <th className="text-left pb-2 pr-4 font-medium">Name</th>
              <th className="text-left pb-2 pr-4 font-medium">Status</th>
              <th className="text-left pb-2 pr-4 font-medium">Ready</th>
              <th className="text-left pb-2 pr-4 font-medium">Restarts</th>
              <th className="text-left pb-2 font-medium">Age</th>
            </tr>
          </thead>
          <tbody>
            {(pods ?? []).map((pod) => (
              <tr
                key={`${pod.namespace}/${pod.name}`}
                className={cn(
                  "border-b border-kn-border/50 hover:bg-kn-bg-elevated cursor-pointer transition-colors",
                  selectedPod?.name === pod.name && "bg-kn-bg-elevated"
                )}
                onClick={() => setSelectedPod(pod)}
                data-testid="pod-row"
              >
                <td className="py-2 pr-4">
                  <span className="text-kn-text-primary font-mono">{pod.name}</span>
                  <span className="text-kn-text-muted ml-1">/{pod.namespace}</span>
                </td>
                <td className="py-2 pr-4">
                  <ResourceBadge status={pod.status} />
                </td>
                <td className="py-2 pr-4 text-kn-text-muted">{pod.ready}</td>
                <td className="py-2 pr-4 text-kn-text-muted">{pod.restarts}</td>
                <td className="py-2 text-kn-text-muted">{pod.age}</td>
              </tr>
            ))}
            {(pods ?? []).length === 0 && (
              <tr>
                <td colSpan={5} className="py-6 text-center text-kn-text-muted">
                  No pods found in this namespace.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {selectedPod && (
        <LogViewer
          namespace={selectedPod.namespace}
          pod={selectedPod.name}
          container={selectedPod.containers[0]?.name ?? "_"}
          clusterContext={activeCluster}
          onClose={() => setSelectedPod(null)}
        />
      )}
    </>
  );
}
