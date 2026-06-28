/**
 * @file Zustand store for active cluster and namespace state.
 *
 * Active cluster and namespace are persisted to localStorage so users
 * don't have to re-select them on page reload.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ClusterContext } from "@/types/cluster";

interface ClusterState {
  /** Active kubeconfig context name. */
  activeCluster: string;
  /** Active Kubernetes namespace. */
  activeNamespace: string;
  /** All available kubeconfig contexts. */
  availableContexts: ClusterContext[];

  setActiveCluster: (cluster: string) => void;
  setActiveNamespace: (namespace: string) => void;
  setAvailableContexts: (contexts: ClusterContext[]) => void;
}

export const useClusterStore = create<ClusterState>()(
  persist(
    (set) => ({
      activeCluster: "",
      activeNamespace: "default",
      availableContexts: [],

      setActiveCluster: (cluster) =>
        set({ activeCluster: cluster, activeNamespace: "default" }),

      setActiveNamespace: (namespace) => set({ activeNamespace: namespace }),

      setAvailableContexts: (contexts) => {
        set({ availableContexts: contexts });
        // Auto-select the active context if none is set.
        const active = contexts.find((c) => c.is_active);
        if (active) {
          set((state) =>
            state.activeCluster ? {} : { activeCluster: active.name }
          );
        }
      },
    }),
    {
      name: "kubenova-cluster",
      partialize: (state: ClusterState) => ({
        activeCluster: state.activeCluster,
        activeNamespace: state.activeNamespace,
      }),
    }
  )
);
