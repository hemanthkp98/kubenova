"""
Pydantic v2 models for cluster context and status data.

Used by the /clusters and /resources endpoints to communicate cluster
metadata and resource summaries to the frontend.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ClusterContext(BaseModel):
    """A single kubeconfig context entry."""

    name: str = Field(description="Context name as defined in kubeconfig.")
    cluster: str = Field(description="Cluster server address or alias.")
    user: str = Field(description="User entry name from kubeconfig.")
    namespace: str = Field(default="default", description="Default namespace for this context.")
    is_active: bool = Field(default=False, description="Whether this is the currently active context.")


class ClusterStatus(BaseModel):
    """High-level health status of a cluster."""

    context_name: str
    server: str
    reachable: bool = Field(description="Whether the API server is reachable.")
    node_count: int = Field(default=0)
    pod_count: int = Field(default=0)
    version: str | None = Field(default=None, description="Kubernetes server version string.")


class ResourceSummary(BaseModel):
    """Aggregate resource counts across all namespaces for dashboard widgets."""

    total_pods: int = 0
    running_pods: int = 0
    failed_pods: int = 0
    pending_pods: int = 0
    total_deployments: int = 0
    total_services: int = 0
    total_nodes: int = 0
    ready_nodes: int = 0
