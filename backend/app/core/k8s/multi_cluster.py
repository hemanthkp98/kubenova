"""
Multi-cluster manager.

Enumerates all kubeconfig contexts and tracks which one is currently active.
The active context is stored per-process; in a multi-worker deployment each
worker maintains its own state (use sticky sessions or a shared cache for HA).
"""

from __future__ import annotations

from loguru import logger
from kubernetes import config as k8s_config  # type: ignore[import]

from app.config import get_settings
from app.core.k8s.client import clear_client_cache, get_k8s_clients
from app.models.cluster import ClusterContext, ClusterStatus


class ClusterManager:
    """Manages available kubeconfig contexts and the active cluster selection."""

    def __init__(self) -> None:
        self._active_context: str | None = None

    def list_contexts(self) -> list[ClusterContext]:
        """
        Return all contexts found in the kubeconfig file.

        Returns:
            List of ClusterContext objects, with is_active set on the current context.
        """
        settings = get_settings()
        try:
            contexts_raw, active_context_raw = k8s_config.list_kube_config_contexts(
                config_file=settings.KUBECONFIG_PATH
            )
        except k8s_config.config_exception.ConfigException as exc:
            logger.warning("Could not load kubeconfig contexts: {}", exc)
            return []

        active_name = (
            self._active_context
            or (active_context_raw["name"] if active_context_raw else None)
        )

        contexts: list[ClusterContext] = []
        for ctx in contexts_raw:
            name = ctx["name"]
            context_info = ctx.get("context", {})
            contexts.append(
                ClusterContext(
                    name=name,
                    cluster=context_info.get("cluster", ""),
                    user=context_info.get("user", ""),
                    namespace=context_info.get("namespace", "default"),
                    is_active=(name == active_name),
                )
            )
        return contexts

    def get_active_context(self) -> str | None:
        """Return the name of the currently active kubeconfig context."""
        if self._active_context:
            return self._active_context

        settings = get_settings()
        if settings.DEFAULT_CLUSTER_CONTEXT:
            return settings.DEFAULT_CLUSTER_CONTEXT

        try:
            _, active = k8s_config.list_kube_config_contexts(
                config_file=settings.KUBECONFIG_PATH
            )
            return active["name"] if active else None
        except Exception:
            return None

    def switch_context(self, context_name: str) -> ClusterContext:
        """
        Switch the active cluster context.

        Clears the client cache so the next request gets fresh clients
        for the new context.

        Args:
            context_name: Name of the kubeconfig context to activate.

        Returns:
            The newly activated ClusterContext.

        Raises:
            ValueError: If the context does not exist in the kubeconfig.
        """
        all_contexts = self.list_contexts()
        names = {c.name for c in all_contexts}
        if context_name not in names:
            raise ValueError(
                f"Context '{context_name}' not found. Available: {sorted(names)}"
            )

        self._active_context = context_name
        clear_client_cache()
        logger.info("Switched active cluster context to '{}'.", context_name)

        for ctx in all_contexts:
            ctx.is_active = ctx.name == context_name

        return next(c for c in all_contexts if c.name == context_name)

    def get_cluster_status(self, context_name: str) -> ClusterStatus:
        """
        Probe the cluster API server and return a health summary.

        Args:
            context_name: kubeconfig context to inspect.

        Returns:
            ClusterStatus with reachability flag and basic counts.
        """
        try:
            clients = get_k8s_clients(context=context_name)
            version_api = clients["core"].api_client.call_api(
                "/version", "GET", response_type="object"
            )
            version_str = version_api[0].get("gitVersion", "unknown")

            nodes = clients["core"].list_node()
            pods = clients["core"].list_pod_for_all_namespaces()

            return ClusterStatus(
                context_name=context_name,
                server=context_name,
                reachable=True,
                node_count=len(nodes.items),
                pod_count=len(pods.items),
                version=version_str,
            )
        except Exception as exc:
            logger.warning("Cluster '{}' is unreachable: {}", context_name, exc)
            return ClusterStatus(
                context_name=context_name,
                server=context_name,
                reachable=False,
            )


# Module-level singleton used by FastAPI dependency injection.
cluster_manager = ClusterManager()
