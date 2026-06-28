/**
 * @file Axios instance and typed API request helpers.
 *
 * The base URL is read from the VITE_API_BASE_URL environment variable,
 * falling back to an empty string (which uses the Vite proxy in dev).
 *
 * LLM API keys are injected from the llmStore per-request via the
 * request interceptor — they are never stored in localStorage.
 */

import axios, { type AxiosInstance } from "axios";
import type { ChatRequest, ChatResponse, ApprovalRequest, ApprovalResponse } from "@/types/chat";
import type { ClusterContext, ClusterStatus } from "@/types/cluster";
import type { PodInfo, DeploymentInfo, ServiceInfo, NodeInfo, EventInfo, PaginatedAuditEvents } from "@/types/resource";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export const apiClient: AxiosInstance = axios.create({
  baseURL: `${BASE_URL}/api`,
  timeout: 30_000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ---------------------------------------------------------------------------
// Chat API
// ---------------------------------------------------------------------------

export const chatApi = {
  sendMessage: (req: ChatRequest): Promise<ChatResponse> =>
    apiClient.post<ChatResponse>("/chat", req).then((r) => r.data),

  approveCommand: (req: ApprovalRequest): Promise<ApprovalResponse> =>
    apiClient.post<ApprovalResponse>("/chat/approve", req).then((r) => r.data),
};

// ---------------------------------------------------------------------------
// Clusters API
// ---------------------------------------------------------------------------

export const clustersApi = {
  list: (): Promise<ClusterContext[]> =>
    apiClient.get<ClusterContext[]>("/clusters").then((r) => r.data),

  getStatus: (name: string): Promise<ClusterStatus> =>
    apiClient.get<ClusterStatus>(`/clusters/${encodeURIComponent(name)}/status`).then((r) => r.data),

  switchContext: (contextName: string): Promise<ClusterContext> =>
    apiClient.post<ClusterContext>("/clusters/switch", { context_name: contextName }).then((r) => r.data),
};

// ---------------------------------------------------------------------------
// Resources API
// ---------------------------------------------------------------------------

export const resourcesApi = {
  listPods: (clusterContext: string, namespace = "default", labelSelector = ""): Promise<PodInfo[]> =>
    apiClient
      .get<PodInfo[]>("/resources/pods", { params: { cluster_context: clusterContext, namespace, label_selector: labelSelector } })
      .then((r) => r.data),

  listDeployments: (clusterContext: string, namespace = "default"): Promise<DeploymentInfo[]> =>
    apiClient
      .get<DeploymentInfo[]>("/resources/deployments", { params: { cluster_context: clusterContext, namespace } })
      .then((r) => r.data),

  listServices: (clusterContext: string, namespace = "default"): Promise<ServiceInfo[]> =>
    apiClient
      .get<ServiceInfo[]>("/resources/services", { params: { cluster_context: clusterContext, namespace } })
      .then((r) => r.data),

  listNodes: (clusterContext: string): Promise<NodeInfo[]> =>
    apiClient
      .get<NodeInfo[]>("/resources/nodes", { params: { cluster_context: clusterContext } })
      .then((r) => r.data),

  listNamespaces: (clusterContext: string): Promise<string[]> =>
    apiClient
      .get<string[]>("/resources/namespaces", { params: { cluster_context: clusterContext } })
      .then((r) => r.data),

  listEvents: (clusterContext: string, namespace = "default"): Promise<EventInfo[]> =>
    apiClient
      .get<EventInfo[]>("/resources/events", { params: { cluster_context: clusterContext, namespace } })
      .then((r) => r.data),
};

// ---------------------------------------------------------------------------
// Audit API
// ---------------------------------------------------------------------------

export const auditApi = {
  list: (params: {
    page?: number;
    page_size?: number;
    cluster_context?: string;
    risk_level?: string;
    from_date?: string;
    to_date?: string;
  }): Promise<PaginatedAuditEvents> =>
    apiClient.get<PaginatedAuditEvents>("/audit", { params }).then((r) => r.data),

  exportCsvUrl: (params?: Record<string, string>): string => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return `${BASE_URL}/api/audit/export${qs}`;
  },
};
