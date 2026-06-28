"""
Kubernetes resource fetcher.

Provides high-level methods for listing and describing common Kubernetes
resources. All methods accept a cluster_context parameter and use the
cached client factory so context switching is transparent.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from loguru import logger

from app.core.k8s.client import get_k8s_clients
from app.models.resource import (
    ContainerInfo,
    DeploymentCondition,
    DeploymentInfo,
    EventInfo,
    NodeCondition,
    NodeInfo,
    PodInfo,
    ServiceInfo,
    ServicePort,
)


def _age(created_at: datetime | None) -> str:
    """Return a human-readable age string from a creation timestamp."""
    if created_at is None:
        return "unknown"
    now = datetime.now(tz=timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    delta = now - created_at
    total_seconds = int(delta.total_seconds())
    if total_seconds < 60:
        return f"{total_seconds}s"
    if total_seconds < 3600:
        return f"{total_seconds // 60}m"
    if total_seconds < 86400:
        return f"{total_seconds // 3600}h"
    return f"{total_seconds // 86400}d"


class ResourceFetcher:
    """Fetches and normalises Kubernetes resource data for the API layer."""

    def list_pods(
        self,
        namespace: str,
        cluster_context: str,
        label_selector: str = "",
    ) -> list[PodInfo]:
        """
        List pods in a namespace.

        Args:
            namespace: Kubernetes namespace. Use 'all' for all namespaces.
            cluster_context: kubeconfig context name.
            label_selector: Optional label selector string.

        Returns:
            List of PodInfo objects.
        """
        clients = get_k8s_clients(context=cluster_context)
        try:
            if namespace == "all":
                raw = clients["core"].list_pod_for_all_namespaces(
                    label_selector=label_selector or None
                )
            else:
                raw = clients["core"].list_namespaced_pod(
                    namespace=namespace,
                    label_selector=label_selector or None,
                )
        except Exception as exc:
            logger.error("Failed to list pods in '{}': {}", namespace, exc)
            return []

        pods: list[PodInfo] = []
        for pod in raw.items:
            containers = self._extract_containers(pod)
            ready_count = sum(1 for c in containers if c.ready)
            total_count = len(containers)
            restarts = sum(c.restart_count for c in containers)
            pods.append(
                PodInfo(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                    status=pod.status.phase or "Unknown",
                    ready=f"{ready_count}/{total_count}",
                    restarts=restarts,
                    age=_age(pod.metadata.creation_timestamp),
                    node=pod.spec.node_name,
                    labels=pod.metadata.labels or {},
                    containers=containers,
                    created_at=pod.metadata.creation_timestamp,
                )
            )
        return pods

    def _extract_containers(self, pod: Any) -> list[ContainerInfo]:
        """Extract ContainerInfo objects from a raw pod object."""
        infos: list[ContainerInfo] = []
        statuses = {s.name: s for s in (pod.status.container_statuses or [])}
        for spec in pod.spec.containers:
            status = statuses.get(spec.name)
            if status is None:
                infos.append(
                    ContainerInfo(
                        name=spec.name,
                        image=spec.image or "",
                        ready=False,
                        restart_count=0,
                        state="Waiting",
                    )
                )
                continue

            state = "Unknown"
            state_reason: str | None = None
            if status.state:
                if status.state.running:
                    state = "Running"
                elif status.state.waiting:
                    state = "Waiting"
                    state_reason = status.state.waiting.reason
                elif status.state.terminated:
                    state = "Terminated"
                    state_reason = status.state.terminated.reason

            infos.append(
                ContainerInfo(
                    name=spec.name,
                    image=spec.image or "",
                    ready=status.ready or False,
                    restart_count=status.restart_count or 0,
                    state=state,
                    state_reason=state_reason,
                )
            )
        return infos

    def describe_pod(
        self, pod_name: str, namespace: str, cluster_context: str
    ) -> str:
        """
        Return a text description of a pod (equivalent to kubectl describe pod).

        Args:
            pod_name: Name of the pod.
            namespace: Namespace of the pod.
            cluster_context: kubeconfig context name.

        Returns:
            Multi-line string description.
        """
        clients = get_k8s_clients(context=cluster_context)
        try:
            pod = clients["core"].read_namespaced_pod(name=pod_name, namespace=namespace)
        except Exception as exc:
            return f"Error: could not describe pod '{pod_name}': {exc}"

        lines: list[str] = [
            f"Name:         {pod.metadata.name}",
            f"Namespace:    {pod.metadata.namespace}",
            f"Node:         {pod.spec.node_name}",
            f"Status:       {pod.status.phase}",
            f"IP:           {pod.status.pod_ip}",
            f"Age:          {_age(pod.metadata.creation_timestamp)}",
            "Labels:",
        ]
        for k, v in (pod.metadata.labels or {}).items():
            lines.append(f"  {k}={v}")
        lines.append("Containers:")
        for c in pod.spec.containers:
            lines.append(f"  {c.name}:")
            lines.append(f"    Image: {c.image}")
        return "\n".join(lines)

    def list_deployments(
        self, namespace: str, cluster_context: str
    ) -> list[DeploymentInfo]:
        """
        List deployments in a namespace.

        Args:
            namespace: Kubernetes namespace. Use 'all' for all namespaces.
            cluster_context: kubeconfig context name.

        Returns:
            List of DeploymentInfo objects.
        """
        clients = get_k8s_clients(context=cluster_context)
        try:
            if namespace == "all":
                raw = clients["apps"].list_deployment_for_all_namespaces()
            else:
                raw = clients["apps"].list_namespaced_deployment(namespace=namespace)
        except Exception as exc:
            logger.error("Failed to list deployments: {}", exc)
            return []

        results: list[DeploymentInfo] = []
        for d in raw.items:
            spec = d.spec
            status = d.status
            images = [c.image for c in (spec.template.spec.containers or [])]
            conditions = [
                DeploymentCondition(
                    type=c.type,
                    status=c.status,
                    reason=c.reason,
                    message=c.message,
                )
                for c in (status.conditions or [])
            ]
            results.append(
                DeploymentInfo(
                    name=d.metadata.name,
                    namespace=d.metadata.namespace,
                    desired=spec.replicas or 0,
                    ready=status.ready_replicas or 0,
                    available=status.available_replicas or 0,
                    updated=status.updated_replicas or 0,
                    age=_age(d.metadata.creation_timestamp),
                    images=images,
                    conditions=conditions,
                    labels=d.metadata.labels or {},
                    created_at=d.metadata.creation_timestamp,
                )
            )
        return results

    def list_services(
        self, namespace: str, cluster_context: str
    ) -> list[ServiceInfo]:
        """
        List services in a namespace.

        Args:
            namespace: Kubernetes namespace. Use 'all' for all namespaces.
            cluster_context: kubeconfig context name.

        Returns:
            List of ServiceInfo objects.
        """
        clients = get_k8s_clients(context=cluster_context)
        try:
            if namespace == "all":
                raw = clients["core"].list_service_for_all_namespaces()
            else:
                raw = clients["core"].list_namespaced_service(namespace=namespace)
        except Exception as exc:
            logger.error("Failed to list services: {}", exc)
            return []

        results: list[ServiceInfo] = []
        for svc in raw.items:
            spec = svc.spec
            ports = [
                ServicePort(
                    name=p.name,
                    protocol=p.protocol or "TCP",
                    port=p.port,
                    target_port=str(p.target_port) if p.target_port else None,
                    node_port=p.node_port,
                )
                for p in (spec.ports or [])
            ]
            external_ips = spec.external_i_ps or []
            lb_ips = [
                ing.ip or ing.hostname
                for ing in (
                    (svc.status.load_balancer.ingress or [])
                    if svc.status and svc.status.load_balancer
                    else []
                )
            ]
            external_ip = (external_ips + lb_ips or [None])[0]

            results.append(
                ServiceInfo(
                    name=svc.metadata.name,
                    namespace=svc.metadata.namespace,
                    type=spec.type or "ClusterIP",
                    cluster_ip=spec.cluster_ip,
                    external_ip=external_ip,
                    ports=ports,
                    selector=spec.selector or {},
                    age=_age(svc.metadata.creation_timestamp),
                    created_at=svc.metadata.creation_timestamp,
                )
            )
        return results

    def list_nodes(self, cluster_context: str) -> list[NodeInfo]:
        """
        List all nodes in the cluster.

        Args:
            cluster_context: kubeconfig context name.

        Returns:
            List of NodeInfo objects.
        """
        clients = get_k8s_clients(context=cluster_context)
        try:
            raw = clients["core"].list_node()
        except Exception as exc:
            logger.error("Failed to list nodes: {}", exc)
            return []

        results: list[NodeInfo] = []
        for node in raw.items:
            labels = node.metadata.labels or {}
            roles = [
                k.split("/")[-1]
                for k in labels
                if k.startswith("node-role.kubernetes.io/")
            ]
            conditions = [
                NodeCondition(
                    type=c.type,
                    status=c.status,
                    reason=c.reason,
                    message=c.message,
                )
                for c in (node.status.conditions or [])
            ]
            ready_status = next(
                (c.status for c in conditions if c.type == "Ready"), "Unknown"
            )
            status_str = "Ready" if ready_status == "True" else "NotReady"
            capacity = node.status.capacity or {}
            info = node.status.node_info

            results.append(
                NodeInfo(
                    name=node.metadata.name,
                    status=status_str,
                    roles=roles or ["worker"],
                    age=_age(node.metadata.creation_timestamp),
                    version=info.kubelet_version if info else "unknown",
                    os_image=info.os_image if info else None,
                    kernel_version=info.kernel_version if info else None,
                    container_runtime=info.container_runtime_version if info else None,
                    cpu_capacity=capacity.get("cpu"),
                    memory_capacity=capacity.get("memory"),
                    conditions=conditions,
                    unschedulable=node.spec.unschedulable or False,
                )
            )
        return results

    def list_events(
        self,
        namespace: str,
        cluster_context: str,
        field_selector: str = "",
    ) -> list[EventInfo]:
        """
        List events in a namespace.

        Args:
            namespace: Kubernetes namespace.
            cluster_context: kubeconfig context name.
            field_selector: Optional field selector string.

        Returns:
            List of EventInfo objects, sorted by last timestamp descending.
        """
        clients = get_k8s_clients(context=cluster_context)
        try:
            if namespace == "all":
                raw = clients["core"].list_event_for_all_namespaces(
                    field_selector=field_selector or None
                )
            else:
                raw = clients["core"].list_namespaced_event(
                    namespace=namespace,
                    field_selector=field_selector or None,
                )
        except Exception as exc:
            logger.error("Failed to list events: {}", exc)
            return []

        events: list[EventInfo] = []
        for ev in raw.items:
            events.append(
                EventInfo(
                    name=ev.metadata.name,
                    namespace=ev.metadata.namespace,
                    type=ev.type or "Normal",
                    reason=ev.reason or "",
                    message=ev.message or "",
                    involved_object_kind=ev.involved_object.kind or "",
                    involved_object_name=ev.involved_object.name or "",
                    count=ev.count or 1,
                    first_time=ev.first_timestamp,
                    last_time=ev.last_timestamp,
                    source_component=ev.source.component if ev.source else None,
                    source_host=ev.source.host if ev.source else None,
                )
            )

        events.sort(key=lambda e: e.last_time or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        return events

    def list_namespaces(self, cluster_context: str) -> list[str]:
        """
        Return all namespace names in the cluster.

        Args:
            cluster_context: kubeconfig context name.

        Returns:
            Sorted list of namespace name strings.
        """
        clients = get_k8s_clients(context=cluster_context)
        try:
            raw = clients["core"].list_namespace()
            return sorted(ns.metadata.name for ns in raw.items)
        except Exception as exc:
            logger.error("Failed to list namespaces: {}", exc)
            return []


# Module-level singleton.
resource_fetcher = ResourceFetcher()
