"""
Kubernetes resource listing API routes.

All endpoints are read-only and require a cluster_context query parameter.
Namespace defaults to 'default'; pass 'all' for cross-namespace queries.

GET /api/resources/pods
GET /api/resources/deployments
GET /api/resources/services
GET /api/resources/nodes
GET /api/resources/namespaces
GET /api/resources/events
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.k8s.resources import resource_fetcher
from app.models.resource import (
    DeploymentInfo,
    EventInfo,
    NodeInfo,
    PodInfo,
    ServiceInfo,
)

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("/pods", response_model=list[PodInfo])
def list_pods(
    cluster_context: str = Query(..., description="kubeconfig context name."),
    namespace: str = Query(default="default", description="Namespace or 'all'."),
    label_selector: str = Query(default="", description="Optional label selector."),
) -> list[PodInfo]:
    """List pods in the given namespace."""
    return resource_fetcher.list_pods(
        namespace=namespace,
        cluster_context=cluster_context,
        label_selector=label_selector,
    )


@router.get("/deployments", response_model=list[DeploymentInfo])
def list_deployments(
    cluster_context: str = Query(..., description="kubeconfig context name."),
    namespace: str = Query(default="default", description="Namespace or 'all'."),
) -> list[DeploymentInfo]:
    """List deployments in the given namespace."""
    return resource_fetcher.list_deployments(
        namespace=namespace,
        cluster_context=cluster_context,
    )


@router.get("/services", response_model=list[ServiceInfo])
def list_services(
    cluster_context: str = Query(..., description="kubeconfig context name."),
    namespace: str = Query(default="default", description="Namespace or 'all'."),
) -> list[ServiceInfo]:
    """List services in the given namespace."""
    return resource_fetcher.list_services(
        namespace=namespace,
        cluster_context=cluster_context,
    )


@router.get("/nodes", response_model=list[NodeInfo])
def list_nodes(
    cluster_context: str = Query(..., description="kubeconfig context name."),
) -> list[NodeInfo]:
    """List all nodes in the cluster."""
    return resource_fetcher.list_nodes(cluster_context=cluster_context)


@router.get("/namespaces", response_model=list[str])
def list_namespaces(
    cluster_context: str = Query(..., description="kubeconfig context name."),
) -> list[str]:
    """List all namespace names in the cluster."""
    return resource_fetcher.list_namespaces(cluster_context=cluster_context)


@router.get("/events", response_model=list[EventInfo])
def list_events(
    cluster_context: str = Query(..., description="kubeconfig context name."),
    namespace: str = Query(default="default", description="Namespace or 'all'."),
    field_selector: str = Query(default="", description="Optional field selector."),
) -> list[EventInfo]:
    """List recent events in the given namespace, sorted by most recent first."""
    return resource_fetcher.list_events(
        namespace=namespace,
        cluster_context=cluster_context,
        field_selector=field_selector,
    )
