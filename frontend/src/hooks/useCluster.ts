/**
 * @file Hook for active cluster and namespace state with persistence.
 *
 * Wraps the clusterStore and provides the initial cluster fetch.
 * Namespace resets to "default" when the cluster changes.
 */

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useClusterStore } from "@/store/clusterStore";
import { clustersApi } from "@/lib/api";

export function useCluster() {
  const {
    activeCluster,
    activeNamespace,
    availableContexts,
    setActiveCluster,
    setActiveNamespace,
    setAvailableContexts,
  } = useClusterStore();

  // Fetch available contexts once on mount.
  const { data: contexts, isLoading, error } = useQuery({
    queryKey: ["clusters"],
    queryFn: clustersApi.list,
    staleTime: 30_000,
  });

  useEffect(() => {
    if (contexts) {
      setAvailableContexts(contexts);
    }
  }, [contexts, setAvailableContexts]);

  const switchCluster = async (name: string) => {
    await clustersApi.switchContext(name);
    setActiveCluster(name);
  };

  return {
    activeCluster,
    activeNamespace,
    availableContexts: contexts ?? availableContexts,
    isLoading,
    error,
    setActiveCluster: switchCluster,
    setActiveNamespace,
  };
}
