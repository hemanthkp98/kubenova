"""
Pydantic v2 models for Kubernetes resource objects returned by the API.

These are deliberately flat representations optimised for the frontend
resource panel — not 1:1 replicas of the full k8s API object schema.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ContainerInfo(BaseModel):
    """Summarised information about a single container within a pod."""

    name: str
    image: str
    ready: bool
    restart_count: int
    state: str = Field(description="Simplified state string: Running, Waiting, Terminated.")
    state_reason: str | None = None


class PodInfo(BaseModel):
    """Summarised pod information for the resource panel."""

    name: str
    namespace: str
    status: str = Field(description="Pod phase: Running, Pending, Failed, Succeeded, Unknown.")
    ready: str = Field(description="Ready containers ratio string, e.g. '2/3'.")
    restarts: int = Field(description="Total restart count across all containers.")
    age: str = Field(description="Human-readable age string, e.g. '2d3h'.")
    node: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    containers: list[ContainerInfo] = Field(default_factory=list)
    created_at: datetime | None = None


class DeploymentCondition(BaseModel):
    """A single condition from a Deployment's status."""

    type: str
    status: str
    reason: str | None = None
    message: str | None = None


class DeploymentInfo(BaseModel):
    """Summarised deployment information for the resource panel."""

    name: str
    namespace: str
    desired: int = Field(description="Desired replica count.")
    ready: int = Field(description="Number of ready replicas.")
    available: int = Field(description="Number of available replicas.")
    updated: int = Field(description="Number of updated replicas.")
    age: str
    images: list[str] = Field(default_factory=list, description="Container image(s) in use.")
    conditions: list[DeploymentCondition] = Field(default_factory=list)
    labels: dict[str, str] = Field(default_factory=dict)
    created_at: datetime | None = None


class ServicePort(BaseModel):
    """A single port exposed by a Service."""

    name: str | None = None
    protocol: str = "TCP"
    port: int
    target_port: str | int | None = None
    node_port: int | None = None


class ServiceInfo(BaseModel):
    """Summarised service information for the resource panel."""

    name: str
    namespace: str
    type: str = Field(description="Service type: ClusterIP, NodePort, LoadBalancer, ExternalName.")
    cluster_ip: str | None = None
    external_ip: str | None = None
    ports: list[ServicePort] = Field(default_factory=list)
    selector: dict[str, str] = Field(default_factory=dict)
    age: str
    created_at: datetime | None = None


class NodeCondition(BaseModel):
    """A single condition from a Node's status."""

    type: str
    status: str
    reason: str | None = None
    message: str | None = None


class NodeInfo(BaseModel):
    """Summarised node information for the resource panel."""

    name: str
    status: str = Field(description="Ready | NotReady | Unknown.")
    roles: list[str] = Field(default_factory=list)
    age: str
    version: str = Field(description="Kubelet version.")
    os_image: str | None = None
    kernel_version: str | None = None
    container_runtime: str | None = None
    cpu_capacity: str | None = None
    memory_capacity: str | None = None
    conditions: list[NodeCondition] = Field(default_factory=list)
    unschedulable: bool = False


class EventInfo(BaseModel):
    """A single Kubernetes event."""

    name: str
    namespace: str
    type: str = Field(description="Normal | Warning.")
    reason: str
    message: str
    involved_object_kind: str
    involved_object_name: str
    count: int = 1
    first_time: datetime | None = None
    last_time: datetime | None = None
    source_component: str | None = None
    source_host: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
