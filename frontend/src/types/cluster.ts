/**
 * @file TypeScript interfaces for cluster context and status data.
 */

export interface ClusterContext {
  name: string;
  cluster: string;
  user: string;
  namespace: string;
  is_active: boolean;
}

export interface ClusterStatus {
  context_name: string;
  server: string;
  reachable: boolean;
  node_count: number;
  pod_count: number;
  version: string | null;
}

export interface ResourceSummary {
  total_pods: number;
  running_pods: number;
  failed_pods: number;
  pending_pods: number;
  total_deployments: number;
  total_services: number;
  total_nodes: number;
  ready_nodes: number;
}
