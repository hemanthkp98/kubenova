"""
Unit tests for app.core.k8s.multi_cluster.ClusterManager.

The kubernetes config loader and client factory are mocked throughout.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.k8s.multi_cluster import ClusterManager


_FAKE_CONTEXTS = [
    {
        "name": "minikube",
        "context": {"cluster": "minikube", "user": "minikube", "namespace": "default"},
    },
    {
        "name": "production",
        "context": {"cluster": "prod-k8s", "user": "admin", "namespace": "production"},
    },
]

_FAKE_ACTIVE = {"name": "minikube"}


def _patch_list_kube_config(contexts=_FAKE_CONTEXTS, active=_FAKE_ACTIVE):
    return patch(
        "app.core.k8s.multi_cluster.k8s_config.list_kube_config_contexts",
        return_value=(contexts, active),
    )


class TestListContexts:
    """Tests for ClusterManager.list_contexts()."""

    def test_returns_all_contexts(self) -> None:
        """All contexts from kubeconfig are returned."""
        manager = ClusterManager()
        with _patch_list_kube_config():
            contexts = manager.list_contexts()
        assert len(contexts) == 2

    def test_active_context_flagged(self) -> None:
        """The active context has is_active=True."""
        manager = ClusterManager()
        with _patch_list_kube_config():
            contexts = manager.list_contexts()
        active = [c for c in contexts if c.is_active]
        assert len(active) == 1
        assert active[0].name == "minikube"

    def test_empty_kubeconfig_returns_empty(self) -> None:
        """If kubeconfig can't be loaded, an empty list is returned."""
        from kubernetes.config.config_exception import ConfigException
        manager = ClusterManager()
        with patch(
            "app.core.k8s.multi_cluster.k8s_config.list_kube_config_contexts",
            side_effect=ConfigException("no kubeconfig"),
        ):
            contexts = manager.list_contexts()
        assert contexts == []

    def test_context_names_correct(self) -> None:
        """Context names match what's in the kubeconfig."""
        manager = ClusterManager()
        with _patch_list_kube_config():
            contexts = manager.list_contexts()
        names = {c.name for c in contexts}
        assert names == {"minikube", "production"}


class TestSwitchContext:
    """Tests for ClusterManager.switch_context()."""

    def test_switch_to_valid_context(self) -> None:
        """Switching to a known context returns the activated ClusterContext."""
        manager = ClusterManager()
        with _patch_list_kube_config(), patch("app.core.k8s.multi_cluster.clear_client_cache"):
            result = manager.switch_context("production")
        assert result.name == "production"
        assert result.is_active is True

    def test_switch_to_invalid_context_raises(self) -> None:
        """Switching to an unknown context raises ValueError."""
        manager = ClusterManager()
        with _patch_list_kube_config(), patch("app.core.k8s.multi_cluster.clear_client_cache"):
            with pytest.raises(ValueError, match="not found"):
                manager.switch_context("does-not-exist")

    def test_switch_clears_client_cache(self) -> None:
        """Switching context clears the k8s client cache."""
        manager = ClusterManager()
        with _patch_list_kube_config():
            with patch("app.core.k8s.multi_cluster.clear_client_cache") as mock_clear:
                manager.switch_context("production")
                mock_clear.assert_called_once()

    def test_active_context_updated(self) -> None:
        """After switching, get_active_context() returns the new context."""
        manager = ClusterManager()
        with _patch_list_kube_config(), patch("app.core.k8s.multi_cluster.clear_client_cache"):
            manager.switch_context("production")
        assert manager.get_active_context() == "production"

    def test_only_switched_context_is_active(self) -> None:
        """Only the newly switched context has is_active=True."""
        manager = ClusterManager()
        with _patch_list_kube_config(), patch("app.core.k8s.multi_cluster.clear_client_cache"):
            contexts = manager.switch_context("production")
        assert contexts.is_active is True
