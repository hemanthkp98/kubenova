/**
 * @file TanStack Query hooks for Kubernetes resource data.
 *
 * Each hook polls the backend at a configurable interval and returns
 * the typed resource list. Queries are disabled when no cluster is selected.
 */

import { useQuery } from "@tanstack/react-query";
import { resourcesApi } from "@/lib/api";
import { useClusterStore } from "@/store/clusterStore";

const REFETCH_INTERVAL = 30_000; // 30 seconds

export function usePods(namespace?: string) {
  const { activeCluster, activeNamespace } = useClusterStore();
  const ns = namespace ?? activeNamespace;
  return useQuery({
    queryKey: ["pods", activeCluster, ns],
    queryFn: () => resourcesApi.listPods(activeCluster, ns),
    enabled: Boolean(activeCluster),
    refetchInterval: REFETCH_INTERVAL,
  });
}

export function useDeployments(namespace?: string) {
  const { activeCluster, activeNamespace } = useClusterStore();
  const ns = namespace ?? activeNamespace;
  return useQuery({
    queryKey: ["deployments", activeCluster, ns],
    queryFn: () => resourcesApi.listDeployments(activeCluster, ns),
    enabled: Boolean(activeCluster),
    refetchInterval: REFETCH_INTERVAL,
  });
}

export function useServices(namespace?: string) {
  const { activeCluster, activeNamespace } = useClusterStore();
  const ns = namespace ?? activeNamespace;
  return useQuery({
    queryKey: ["services", activeCluster, ns],
    queryFn: () => resourcesApi.listServices(activeCluster, ns),
    enabled: Boolean(activeCluster),
    refetchInterval: REFETCH_INTERVAL,
  });
}

export function useNodes() {
  const { activeCluster } = useClusterStore();
  return useQuery({
    queryKey: ["nodes", activeCluster],
    queryFn: () => resourcesApi.listNodes(activeCluster),
    enabled: Boolean(activeCluster),
    refetchInterval: REFETCH_INTERVAL,
  });
}

export function useNamespaces() {
  const { activeCluster } = useClusterStore();
  return useQuery({
    queryKey: ["namespaces", activeCluster],
    queryFn: () => resourcesApi.listNamespaces(activeCluster),
    enabled: Boolean(activeCluster),
    staleTime: 60_000,
  });
}

export function useEvents(namespace?: string) {
  const { activeCluster, activeNamespace } = useClusterStore();
  const ns = namespace ?? activeNamespace;
  return useQuery({
    queryKey: ["events", activeCluster, ns],
    queryFn: () => resourcesApi.listEvents(activeCluster, ns),
    enabled: Boolean(activeCluster),
    refetchInterval: REFETCH_INTERVAL,
  });
}
