"""
Cluster management API routes.

GET  /api/clusters               — list all available kubeconfig contexts
GET  /api/clusters/{name}/status — health check for a specific cluster
POST /api/clusters/switch        — change the active context
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_cluster_manager
from app.core.k8s.multi_cluster import ClusterManager
from app.models.cluster import ClusterContext, ClusterStatus

router = APIRouter(prefix="/clusters", tags=["clusters"])


class SwitchContextRequest(BaseModel):
    """Request body for POST /clusters/switch."""

    context_name: str


@router.get("", response_model=list[ClusterContext])
def list_clusters(
    manager: ClusterManager = Depends(get_cluster_manager),
) -> list[ClusterContext]:
    """
    Return all kubeconfig contexts available on the backend host.

    The is_active flag is set on whichever context is currently selected.
    """
    return manager.list_contexts()


@router.get("/{name}/status", response_model=ClusterStatus)
def get_cluster_status(
    name: str,
    manager: ClusterManager = Depends(get_cluster_manager),
) -> ClusterStatus:
    """
    Probe the API server for the named cluster context and return health info.

    The reachable field will be False if the server cannot be contacted.
    """
    return manager.get_cluster_status(context_name=name)


@router.post("/switch", response_model=ClusterContext)
def switch_cluster(
    request: SwitchContextRequest,
    manager: ClusterManager = Depends(get_cluster_manager),
) -> ClusterContext:
    """
    Switch the active cluster context.

    Returns the newly active ClusterContext. Raises 404 if the context
    does not exist in the kubeconfig.
    """
    try:
        return manager.switch_context(request.context_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
