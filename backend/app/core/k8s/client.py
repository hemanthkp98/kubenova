"""
Kubernetes client factory.

Creates and caches kubernetes API clients keyed by kubeconfig context name.
Supports an optional KUBECONFIG_PATH override from settings; falls back to
the default ~/.kube/config location if not set.
"""

from __future__ import annotations

import threading
from typing import Any

from kubernetes import client as k8s_client  # type: ignore[import]
from kubernetes import config as k8s_config  # type: ignore[import]
from loguru import logger

from app.config import get_settings

_client_cache: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()


def get_k8s_clients(context: str | None = None) -> dict[str, Any]:
    """
    Return a dict of kubernetes API client instances for the given context.

    The returned dict contains:
      - ``core``: CoreV1Api
      - ``apps``: AppsV1Api
      - ``batch``: BatchV1Api
      - ``networking``: NetworkingV1Api
      - ``rbac``: RbacAuthorizationV1Api

    Results are cached per context name.

    Args:
        context: kubeconfig context name. Uses the current-context if None.

    Returns:
        Dictionary of typed kubernetes API client instances.
    """
    settings = get_settings()
    cache_key = context or "__current__"

    with _lock:
        if cache_key in _client_cache:
            return _client_cache[cache_key]

        kubeconfig = settings.KUBECONFIG_PATH
        try:
            k8s_config.load_kube_config(config_file=kubeconfig, context=context)
        except k8s_config.config_exception.ConfigException:
            # Fall back to in-cluster config when running inside a pod.
            try:
                k8s_config.load_incluster_config()
                logger.info("Loaded in-cluster Kubernetes configuration.")
            except k8s_config.config_exception.ConfigException as exc:
                raise RuntimeError(
                    "Cannot load Kubernetes configuration. "
                    "Ensure a valid kubeconfig or in-cluster credentials are available."
                ) from exc
        else:
            logger.info("Loaded kubeconfig context: {}", context or "current-context")

        clients: dict[str, Any] = {
            "core": k8s_client.CoreV1Api(),
            "apps": k8s_client.AppsV1Api(),
            "batch": k8s_client.BatchV1Api(),
            "networking": k8s_client.NetworkingV1Api(),
            "rbac": k8s_client.RbacAuthorizationV1Api(),
        }
        _client_cache[cache_key] = clients
        return clients


def clear_client_cache() -> None:
    """Invalidate the cached clients — useful after context switching."""
    with _lock:
        _client_cache.clear()
    logger.debug("Kubernetes client cache cleared.")
