"""
LangChain tool definitions for the KubeNova agent.

Each function decorated with @tool becomes available for the LLM to call.
The docstrings are critical — the LLM reads them to understand when and
how to invoke each tool.

All tools accept explicit cluster_context and namespace parameters so the
agent can operate on multi-cluster environments without ambient globals.
"""

from __future__ import annotations

import json
from typing import Annotated

from langchain_core.tools import tool
from loguru import logger

from app.core.k8s.executor import dry_run_manifest, generate_kubectl_command
from app.core.k8s.resources import resource_fetcher


@tool
def list_pods(
    namespace: Annotated[str, "Kubernetes namespace to search. Use 'all' for all namespaces."],
    cluster_context: Annotated[str, "kubeconfig context name identifying the target cluster."],
    label_selector: Annotated[str, "Optional label selector, e.g. 'app=nginx'. Leave empty for all pods."] = "",
) -> str:
    """
    List all pods in the specified namespace of a Kubernetes cluster.

    Returns a JSON array of pod summaries including name, namespace, status,
    restart count, and container states. Use this to inspect pod health,
    find crashing pods, or locate pods by label.

    Returns a JSON string representing the list of pods.
    """
    pods = resource_fetcher.list_pods(
        namespace=namespace,
        cluster_context=cluster_context,
        label_selector=label_selector,
    )
    result = [p.model_dump(mode="json") for p in pods]
    logger.debug("list_pods: returned {} pods from '{}'/'{}'.", len(result), cluster_context, namespace)
    return json.dumps(result, default=str)


@tool
def describe_pod(
    pod_name: Annotated[str, "Name of the pod to describe."],
    namespace: Annotated[str, "Namespace where the pod lives."],
    cluster_context: Annotated[str, "kubeconfig context name."],
) -> str:
    """
    Get detailed information about a specific pod, similar to 'kubectl describe pod'.

    Returns labels, status, container specs, restart count, and events.
    Use this when diagnosing why a pod is failing or to understand its configuration.

    Returns a multi-line text description of the pod.
    """
    return resource_fetcher.describe_pod(
        pod_name=pod_name,
        namespace=namespace,
        cluster_context=cluster_context,
    )


@tool
def get_pod_logs(
    pod_name: Annotated[str, "Name of the pod to fetch logs from."],
    namespace: Annotated[str, "Namespace of the pod."],
    container: Annotated[str, "Container name within the pod. Use empty string for the default container."],
    cluster_context: Annotated[str, "kubeconfig context name."],
    tail: Annotated[int, "Number of log lines to return from the end. Default 100."] = 100,
) -> str:
    """
    Fetch recent log output from a pod container.

    Returns the last `tail` lines of stdout/stderr from the container.
    Use this to diagnose application errors, startup failures, or runtime exceptions.

    Returns a string containing the log lines.
    """
    from app.core.k8s.client import get_k8s_clients
    from app.config import get_settings

    settings = get_settings()
    tail = min(tail, settings.MAX_LOG_LINES)

    clients = get_k8s_clients(context=cluster_context)
    try:
        kwargs: dict[str, object] = {
            "name": pod_name,
            "namespace": namespace,
            "tail_lines": tail,
            "timestamps": True,
        }
        if container:
            kwargs["container"] = container

        logs = clients["core"].read_namespaced_pod_log(**kwargs)  # type: ignore[arg-type]
        return logs or "(no log output)"
    except Exception as exc:
        return f"Error fetching logs: {exc}"


@tool
def list_deployments(
    namespace: Annotated[str, "Kubernetes namespace. Use 'all' for all namespaces."],
    cluster_context: Annotated[str, "kubeconfig context name."],
) -> str:
    """
    List all deployments in a namespace.

    Returns a JSON array with name, replica counts (desired/ready/available),
    images, and conditions. Use this to find under-replicated or unhealthy deployments.

    Returns a JSON string representing the list of deployments.
    """
    deployments = resource_fetcher.list_deployments(
        namespace=namespace,
        cluster_context=cluster_context,
    )
    return json.dumps([d.model_dump(mode="json") for d in deployments], default=str)


@tool
def describe_deployment(
    name: Annotated[str, "Name of the deployment to describe."],
    namespace: Annotated[str, "Namespace of the deployment."],
    cluster_context: Annotated[str, "kubeconfig context name."],
) -> str:
    """
    Get detailed information about a specific deployment.

    Returns the deployment spec, replica status, strategy, and conditions.
    Use this when investigating rollout failures or misconfigured deployments.

    Returns a JSON string with full deployment details.
    """
    from app.core.k8s.client import get_k8s_clients

    clients = get_k8s_clients(context=cluster_context)
    try:
        d = clients["apps"].read_namespaced_deployment(name=name, namespace=namespace)
        return json.dumps(
            {
                "name": d.metadata.name,
                "namespace": d.metadata.namespace,
                "replicas": d.spec.replicas,
                "ready_replicas": d.status.ready_replicas,
                "strategy": d.spec.strategy.type if d.spec.strategy else None,
                "conditions": [
                    {"type": c.type, "status": c.status, "message": c.message}
                    for c in (d.status.conditions or [])
                ],
            },
            default=str,
        )
    except Exception as exc:
        return f"Error: {exc}"


@tool
def list_events(
    namespace: Annotated[str, "Kubernetes namespace to search."],
    cluster_context: Annotated[str, "kubeconfig context name."],
    field_selector: Annotated[str, "Optional field selector, e.g. 'involvedObject.name=my-pod'."] = "",
) -> str:
    """
    List Kubernetes events in a namespace, sorted by most recent first.

    Events reveal why pods failed to schedule, why containers restarted,
    or why resources failed to be created. Use this for incident diagnosis.

    Returns a JSON string representing the list of events.
    """
    events = resource_fetcher.list_events(
        namespace=namespace,
        cluster_context=cluster_context,
        field_selector=field_selector,
    )
    return json.dumps([e.model_dump(mode="json") for e in events], default=str)


@tool
def exec_kubectl_dry_run(
    manifest_yaml: Annotated[str, "Complete YAML manifest to validate against the cluster."],
    cluster_context: Annotated[str, "kubeconfig context name."],
) -> str:
    """
    Validate a Kubernetes YAML manifest using kubectl --dry-run=server.

    This is a safety check — it runs the operation against the API server
    in simulation mode without making any changes. Returns whether the
    operation would succeed, any diff output, and warnings.

    Use this before suggesting an apply operation to verify the manifest is valid.

    Returns a JSON string with is_safe, diff, warnings, resource_name, resource_kind.
    """
    result = dry_run_manifest(manifest_yaml=manifest_yaml, cluster_context=cluster_context)
    return json.dumps(result.model_dump(), default=str)


@tool
def get_node_status(
    cluster_context: Annotated[str, "kubeconfig context name."],
) -> str:
    """
    List all nodes in the cluster with their health status and resource pressure indicators.

    Returns information about CPU/memory pressure, disk pressure, network availability,
    and scheduling status. Use this when investigating cluster-wide resource issues or
    when pods are failing to schedule.

    Returns a JSON string representing the list of nodes.
    """
    nodes = resource_fetcher.list_nodes(cluster_context=cluster_context)
    return json.dumps([n.model_dump(mode="json") for n in nodes], default=str)


@tool
def list_namespaces(
    cluster_context: Annotated[str, "kubeconfig context name."],
) -> str:
    """
    List all namespaces in the cluster.

    Use this to discover available namespaces when the user hasn't specified one,
    or when you need to search across the entire cluster.

    Returns a JSON string representing a list of namespace name strings.
    """
    namespaces = resource_fetcher.list_namespaces(cluster_context=cluster_context)
    return json.dumps(namespaces)


# The full list of tools registered with the agent.
ALL_TOOLS = [
    list_pods,
    describe_pod,
    get_pod_logs,
    list_deployments,
    describe_deployment,
    list_events,
    exec_kubectl_dry_run,
    get_node_status,
    list_namespaces,
]
