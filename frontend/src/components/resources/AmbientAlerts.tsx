/**
 * @file Ambient alerts — proactive cluster health warnings.
 *
 * Polls GET /resources/pods every 30 seconds. Renders dismissible banners for:
 * - CrashLoopBackOff pods → ask AI to diagnose
 * - Pending pods → ask AI to investigate
 * - Node pressure conditions (polled via GET /resources/nodes)
 *
 * Clicking "Ask AI" pre-fills the chat input focus for the operator.
 */

import { useState } from "react";
import { AlertTriangle, Clock, XCircle, X } from "lucide-react";
import { usePods, useNodes } from "@/hooks/useResources";
import { cn } from "@/lib/utils";

interface AmbientAlertsProps {
  onAskAI?: (message: string) => void;
  className?: string;
}

interface AlertBanner {
  id: string;
  icon: React.ReactNode;
  message: string;
  aiPrompt: string;
  color: string;
}

export function AmbientAlerts({ onAskAI, className }: AmbientAlertsProps) {
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());
  const { data: pods } = usePods();
  const { data: nodes } = useNodes();

  const dismiss = (id: string) => setDismissed((prev) => new Set([...prev, id]));

  const alerts: AlertBanner[] = [];

  // CrashLoopBackOff pods.
  const crashing = (pods ?? []).filter(
    (p) => p.containers.some((c) => c.state_reason === "CrashLoopBackOff") || p.status === "CrashLoopBackOff"
  );
  if (crashing.length > 0) {
    const id = "crash-loop";
    if (!dismissed.has(id)) {
      alerts.push({
        id,
        icon: <XCircle size={14} />,
        message: `${crashing.length} pod(s) in CrashLoopBackOff`,
        aiPrompt: `Diagnose CrashLoopBackOff for pods: ${crashing.map((p) => p.name).join(", ")}`,
        color: "border-kn-danger/40 bg-kn-danger/10 text-kn-danger",
      });
    }
  }

  // Pending pods (simplified: we don't have creation time in PodInfo age field).
  const pending = (pods ?? []).filter((p) => p.status === "Pending");
  if (pending.length > 0) {
    const id = "pending-pods";
    if (!dismissed.has(id)) {
      alerts.push({
        id,
        icon: <Clock size={14} />,
        message: `${pending.length} pod(s) stuck pending`,
        aiPrompt: `Investigate why these pods are stuck in Pending: ${pending.map((p) => p.name).join(", ")}`,
        color: "border-kn-warning/40 bg-kn-warning/10 text-kn-warning",
      });
    }
  }

  // Node pressure.
  for (const node of nodes ?? []) {
    for (const cond of node.conditions) {
      if (
        ["MemoryPressure", "DiskPressure", "PIDPressure"].includes(cond.type) &&
        cond.status === "True"
      ) {
        const id = `node-${node.name}-${cond.type}`;
        if (!dismissed.has(id)) {
          alerts.push({
            id,
            icon: <AlertTriangle size={14} />,
            message: `Node ${node.name} has ${cond.type}`,
            aiPrompt: `Node ${node.name} is showing ${cond.type}=True. Diagnose the issue.`,
            color: "border-kn-danger/40 bg-kn-danger/10 text-kn-danger",
          });
        }
      }
    }
  }

  if (alerts.length === 0) return null;

  return (
    <div className={cn("space-y-1.5", className)}>
      {alerts.map((alert) => (
        <div
          key={alert.id}
          className={cn(
            "flex items-center justify-between px-3 py-2 rounded-md border text-xs",
            alert.color
          )}
          role="alert"
        >
          <div className="flex items-center gap-2">
            {alert.icon}
            <span>{alert.message}</span>
            {onAskAI && (
              <button
                onClick={() => onAskAI(alert.aiPrompt)}
                className="underline underline-offset-2 hover:opacity-80 ml-1"
              >
                Ask AI
              </button>
            )}
          </div>
          <button
            onClick={() => dismiss(alert.id)}
            aria-label="Dismiss alert"
            className="hover:opacity-70"
          >
            <X size={12} />
          </button>
        </div>
      ))}
    </div>
  );
}
