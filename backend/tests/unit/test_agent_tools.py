"""
Unit tests for app.core.agents.tools.

Each LangChain tool is tested with a mocked cluster — no real Kubernetes
API calls are made.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.core.agents.tools import (
    describe_pod,
    exec_kubectl_dry_run,
    get_node_status,
    get_pod_logs,
    list_deployments,
    list_events,
    list_namespaces,
    list_pods,
)
from app.models.resource import PodInfo, DeploymentInfo, NodeInfo, EventInfo


def _patch_fetcher(**kwargs):
    """Patch the resource_fetcher singleton on the tools module."""
    return patch("app.core.agents.tools.resource_fetcher", **kwargs)


class TestListPodsTools:
    """Tests for the list_pods tool."""

    def test_returns_json_string(self) -> None:
        """list_pods returns a JSON string."""
        mock_pod = PodInfo(
            name="nginx",
            namespace="default",
            status="Running",
            ready="1/1",
            restarts=0,
            age="1h",
        )
        with _patch_fetcher() as mock:
            mock.list_pods.return_value = [mock_pod]
            result = list_pods.invoke({"namespace": "default", "cluster_context": "minikube"})

        data = json.loads(result)
        assert isinstance(data, list)
        assert data[0]["name"] == "nginx"

    def test_empty_result_returns_empty_json_array(self) -> None:
        """Empty pod list returns '[]'."""
        with _patch_fetcher() as mock:
            mock.list_pods.return_value = []
            result = list_pods.invoke({"namespace": "default", "cluster_context": "minikube"})
        assert json.loads(result) == []

    def test_label_selector_forwarded(self) -> None:
        """label_selector is passed through to resource_fetcher."""
        with _patch_fetcher() as mock:
            mock.list_pods.return_value = []
            list_pods.invoke({
                "namespace": "default",
                "cluster_context": "minikube",
                "label_selector": "app=nginx",
            })
            mock.list_pods.assert_called_once_with(
                namespace="default",
                cluster_context="minikube",
                label_selector="app=nginx",
            )


class TestDescribePodTool:
    """Tests for the describe_pod tool."""

    def test_returns_string(self) -> None:
        """describe_pod returns a string description."""
        with _patch_fetcher() as mock:
            mock.describe_pod.return_value = "Name: nginx\nNamespace: default"
            result = describe_pod.invoke({
                "pod_name": "nginx",
                "namespace": "default",
                "cluster_context": "minikube",
            })
        assert "nginx" in result


class TestGetPodLogsTool:
    """Tests for the get_pod_logs tool."""

    def test_returns_log_lines(self) -> None:
        """get_pod_logs returns log content."""
        fake_logs = "2024-01-01T00:00:00Z INFO app started\n"
        mock_core = MagicMock()
        mock_core.read_namespaced_pod_log.return_value = fake_logs

        with patch("app.core.agents.tools.get_k8s_clients") as mock_clients:
            mock_clients.return_value = {"core": mock_core}
            result = get_pod_logs.invoke({
                "pod_name": "nginx",
                "namespace": "default",
                "container": "nginx",
                "cluster_context": "minikube",
            })
        assert "INFO app started" in result

    def test_api_error_returns_error_string(self) -> None:
        """API exception returns an error string instead of raising."""
        mock_core = MagicMock()
        mock_core.read_namespaced_pod_log.side_effect = Exception("pod not found")

        with patch("app.core.agents.tools.get_k8s_clients") as mock_clients:
            mock_clients.return_value = {"core": mock_core}
            result = get_pod_logs.invoke({
                "pod_name": "ghost",
                "namespace": "default",
                "container": "",
                "cluster_context": "minikube",
            })
        assert "Error" in result


class TestListNamespacesTool:
    """Tests for the list_namespaces tool."""

    def test_returns_json_list(self) -> None:
        """list_namespaces returns a JSON array of strings."""
        with _patch_fetcher() as mock:
            mock.list_namespaces.return_value = ["default", "kube-system"]
            result = list_namespaces.invoke({"cluster_context": "minikube"})
        data = json.loads(result)
        assert "default" in data


class TestExecDryRunTool:
    """Tests for the exec_kubectl_dry_run tool."""

    def test_returns_json_dict(self) -> None:
        """exec_kubectl_dry_run returns a JSON object."""
        with patch("app.core.agents.tools.dry_run_manifest") as mock_dry:
            from app.core.k8s.executor import DryRunResult
            mock_dry.return_value = DryRunResult(
                is_safe=True,
                diff="+ Deployment/my-app",
                warnings=[],
                resource_name="my-app",
                resource_kind="Deployment",
            )
            result = exec_kubectl_dry_run.invoke({
                "manifest_yaml": "kind: Deployment\nmetadata:\n  name: my-app",
                "cluster_context": "minikube",
            })
        data = json.loads(result)
        assert data["is_safe"] is True
        assert data["resource_name"] == "my-app"
