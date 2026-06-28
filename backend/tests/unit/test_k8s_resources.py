"""
Unit tests for app.core.k8s.resources.ResourceFetcher.

All kubernetes API calls are mocked — no real cluster is needed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.core.k8s.resources import ResourceFetcher, _age


# ---------------------------------------------------------------------------
# _age helper
# ---------------------------------------------------------------------------

class TestAgeHelper:
    """Tests for the _age() time formatting helper."""

    def test_returns_unknown_for_none(self) -> None:
        """None input returns 'unknown'."""
        assert _age(None) == "unknown"

    def test_seconds_format(self) -> None:
        """Less than 60 seconds shows 's' suffix."""
        from datetime import timedelta
        ts = datetime.now(tz=timezone.utc) - timedelta(seconds=30)
        result = _age(ts)
        assert result.endswith("s")

    def test_minutes_format(self) -> None:
        """One to 59 minutes shows 'm' suffix."""
        from datetime import timedelta
        ts = datetime.now(tz=timezone.utc) - timedelta(minutes=5)
        assert _age(ts).endswith("m")

    def test_hours_format(self) -> None:
        """One to 23 hours shows 'h' suffix."""
        from datetime import timedelta
        ts = datetime.now(tz=timezone.utc) - timedelta(hours=3)
        assert _age(ts).endswith("h")

    def test_days_format(self) -> None:
        """24+ hours shows 'd' suffix."""
        from datetime import timedelta
        ts = datetime.now(tz=timezone.utc) - timedelta(days=5)
        assert _age(ts).endswith("d")


# ---------------------------------------------------------------------------
# ResourceFetcher.list_pods
# ---------------------------------------------------------------------------

def _make_pod(name: str, namespace: str = "default", phase: str = "Running") -> MagicMock:
    """Build a minimal mock Pod object."""
    pod = MagicMock()
    pod.metadata.name = name
    pod.metadata.namespace = namespace
    pod.metadata.creation_timestamp = datetime.now(tz=timezone.utc)
    pod.metadata.labels = {"app": name}
    pod.status.phase = phase
    pod.status.pod_ip = "10.0.0.1"
    pod.spec.node_name = "node-1"
    pod.spec.containers = []
    pod.status.container_statuses = []
    return pod


class TestListPods:
    """Tests for ResourceFetcher.list_pods()."""

    def test_returns_pod_list(self) -> None:
        """list_pods returns PodInfo objects for each pod."""
        fetcher = ResourceFetcher()
        raw_response = MagicMock()
        raw_response.items = [_make_pod("nginx"), _make_pod("redis")]

        with patch("app.core.k8s.resources.get_k8s_clients") as mock_clients:
            mock_clients.return_value = {
                "core": MagicMock(list_namespaced_pod=MagicMock(return_value=raw_response))
            }
            pods = fetcher.list_pods(namespace="default", cluster_context="minikube")

        assert len(pods) == 2
        names = {p.name for p in pods}
        assert "nginx" in names
        assert "redis" in names

    def test_empty_namespace_returns_empty(self) -> None:
        """An empty namespace returns an empty list."""
        fetcher = ResourceFetcher()
        raw_response = MagicMock()
        raw_response.items = []

        with patch("app.core.k8s.resources.get_k8s_clients") as mock_clients:
            mock_clients.return_value = {
                "core": MagicMock(list_namespaced_pod=MagicMock(return_value=raw_response))
            }
            pods = fetcher.list_pods(namespace="empty-ns", cluster_context="minikube")

        assert pods == []

    def test_api_exception_returns_empty(self) -> None:
        """An API exception returns an empty list without raising."""
        fetcher = ResourceFetcher()
        with patch("app.core.k8s.resources.get_k8s_clients") as mock_clients:
            mock_clients.return_value = {
                "core": MagicMock(
                    list_namespaced_pod=MagicMock(side_effect=Exception("API error"))
                )
            }
            pods = fetcher.list_pods(namespace="default", cluster_context="minikube")
        assert pods == []

    def test_pod_status_mapped(self) -> None:
        """Pod phase is correctly mapped to PodInfo.status."""
        fetcher = ResourceFetcher()
        raw_response = MagicMock()
        raw_response.items = [_make_pod("failing-pod", phase="Failed")]

        with patch("app.core.k8s.resources.get_k8s_clients") as mock_clients:
            mock_clients.return_value = {
                "core": MagicMock(list_namespaced_pod=MagicMock(return_value=raw_response))
            }
            pods = fetcher.list_pods(namespace="default", cluster_context="minikube")

        assert pods[0].status == "Failed"

    def test_all_namespace_uses_correct_api(self) -> None:
        """Passing namespace='all' calls list_pod_for_all_namespaces."""
        fetcher = ResourceFetcher()
        raw_response = MagicMock()
        raw_response.items = []
        list_all = MagicMock(return_value=raw_response)

        with patch("app.core.k8s.resources.get_k8s_clients") as mock_clients:
            mock_clients.return_value = {
                "core": MagicMock(list_pod_for_all_namespaces=list_all)
            }
            fetcher.list_pods(namespace="all", cluster_context="minikube")

        list_all.assert_called_once()


# ---------------------------------------------------------------------------
# ResourceFetcher.list_namespaces
# ---------------------------------------------------------------------------

class TestListNamespaces:
    """Tests for ResourceFetcher.list_namespaces()."""

    def test_returns_sorted_names(self) -> None:
        """Namespace names are returned sorted alphabetically."""
        fetcher = ResourceFetcher()
        ns_c = MagicMock(); ns_c.metadata.name = "zoo"
        ns_a = MagicMock(); ns_a.metadata.name = "alpha"
        raw = MagicMock(); raw.items = [ns_c, ns_a]

        with patch("app.core.k8s.resources.get_k8s_clients") as mock_clients:
            mock_clients.return_value = {"core": MagicMock(list_namespace=MagicMock(return_value=raw))}
            result = fetcher.list_namespaces(cluster_context="minikube")

        assert result == ["alpha", "zoo"]

    def test_exception_returns_empty(self) -> None:
        """API exception returns empty list."""
        fetcher = ResourceFetcher()
        with patch("app.core.k8s.resources.get_k8s_clients") as mock_clients:
            mock_clients.return_value = {"core": MagicMock(list_namespace=MagicMock(side_effect=Exception))}
            assert fetcher.list_namespaces(cluster_context="minikube") == []
