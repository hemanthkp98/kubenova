/**
 * @file Resource panel — right sidebar with tabbed Kubernetes resource views.
 *
 * Tabs: Pods | Deployments | Services | Nodes
 * AmbientAlerts are shown at the top of the panel when issues are detected.
 */

import { useState } from "react";
import { PodList } from "./PodList";
import { DeploymentList } from "./DeploymentList";
import { ServiceList } from "./ServiceList";
import { NodeList } from "./NodeList";
import { AmbientAlerts } from "./AmbientAlerts";
import { cn } from "@/lib/utils";

type ResourceTab = "pods" | "deployments" | "services" | "nodes";

interface ResourcePanelProps {
  onAskAI?: (message: string) => void;
  className?: string;
}

const TABS: { id: ResourceTab; label: string }[] = [
  { id: "pods", label: "Pods" },
  { id: "deployments", label: "Deploys" },
  { id: "services", label: "Services" },
  { id: "nodes", label: "Nodes" },
];

export function ResourcePanel({ onAskAI, className }: ResourcePanelProps) {
  const [activeTab, setActiveTab] = useState<ResourceTab>("pods");

  return (
    <div className={cn("flex flex-col h-full bg-kn-bg-surface border-l border-kn-border", className)}>
      {/* Header */}
      <div className="px-4 pt-4 pb-2">
        <h2 className="text-xs font-semibold text-kn-text-muted uppercase tracking-wider mb-3">
          Cluster Resources
        </h2>
        <AmbientAlerts onAskAI={onAskAI} />
      </div>

      {/* Tabs */}
      <div className="flex border-b border-kn-border px-4">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "px-3 py-2 text-xs font-medium border-b-2 transition-colors -mb-px",
              activeTab === tab.id
                ? "border-kn-accent text-kn-accent"
                : "border-transparent text-kn-text-muted hover:text-kn-text-primary"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === "pods" && <PodList />}
        {activeTab === "deployments" && <DeploymentList />}
        {activeTab === "services" && <ServiceList />}
        {activeTab === "nodes" && <NodeList />}
      </div>
    </div>
  );
}
