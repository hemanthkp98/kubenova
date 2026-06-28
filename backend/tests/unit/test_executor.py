"""
Unit tests for app.core.k8s.executor.

Tests cover risk classification, dry-run subprocess handling, and
the apply_manifest path. No real kubectl is invoked — subprocess.run
is mocked throughout.
"""

from __future__ import annotations

from subprocess import CompletedProcess
from unittest.mock import MagicMock, patch

import pytest

from app.core.k8s.executor import (
    RiskLevel,
    apply_manifest,
    classify_intent_risk,
    dry_run_manifest,
    generate_kubectl_command,
)

# ---------------------------------------------------------------------------
# classify_intent_risk
# ---------------------------------------------------------------------------


class TestClassifyIntentRisk:
    """Tests for the intent risk classifier."""

    @pytest.mark.parametrize(
        "command,expected",
        [
            ("delete namespace default", RiskLevel.CRITICAL),
            ("kubectl delete namespace production", RiskLevel.CRITICAL),
            ("drain node worker-1", RiskLevel.CRITICAL),
            ("delete node --all", RiskLevel.CRITICAL),
            ("delete deployment web --all", RiskLevel.CRITICAL),
        ],
    )
    def test_critical_patterns(self, command: str, expected: RiskLevel) -> None:
        """CRITICAL-risk patterns are correctly identified."""
        assert classify_intent_risk(command) == expected

    @pytest.mark.parametrize(
        "command,expected",
        [
            ("scale deployment api-server --replicas=0", RiskLevel.HIGH),
            ("kubectl scale deployment web --replicas=0", RiskLevel.HIGH),
            ("delete deployment my-app", RiskLevel.HIGH),
            ("delete statefulset db", RiskLevel.HIGH),
            ("exec -it my-pod -- bash", RiskLevel.HIGH),
        ],
    )
    def test_high_patterns(self, command: str, expected: RiskLevel) -> None:
        """HIGH-risk patterns are correctly identified."""
        assert classify_intent_risk(command) == expected

    @pytest.mark.parametrize(
        "command,expected",
        [
            ("get pods", RiskLevel.LOW),
            ("describe pod nginx-abc123", RiskLevel.LOW),
            ("logs my-pod", RiskLevel.LOW),
            ("kubectl get nodes", RiskLevel.LOW),
        ],
    )
    def test_low_patterns(self, command: str, expected: RiskLevel) -> None:
        """Read-only commands are classified as LOW risk."""
        assert classify_intent_risk(command) == expected

    @pytest.mark.parametrize(
        "command,expected",
        [
            ("apply -f deployment.yaml", RiskLevel.MEDIUM),
            ("create configmap my-config", RiskLevel.MEDIUM),
            ("patch deployment web --patch '{}'", RiskLevel.MEDIUM),
        ],
    )
    def test_medium_patterns(self, command: str, expected: RiskLevel) -> None:
        """Write operations that are not HIGH are MEDIUM."""
        assert classify_intent_risk(command) == expected


# ---------------------------------------------------------------------------
# dry_run_manifest
# ---------------------------------------------------------------------------

_SAMPLE_YAML = """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: app
          image: nginx:latest
"""


class TestDryRunManifest:
    """Tests for dry_run_manifest()."""

    def test_successful_dry_run(self) -> None:
        """dry_run_manifest returns is_safe=True when kubectl exits 0."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"kind": "Deployment", "metadata": {"name": "my-app"}}',
                stderr="",
            )
            result = dry_run_manifest(_SAMPLE_YAML, "minikube")
            assert result.is_safe is True
            assert result.resource_kind == "Deployment"
            assert result.resource_name == "my-app"

    def test_failed_dry_run_returns_unsafe(self) -> None:
        """dry_run_manifest returns is_safe=False when kubectl exits non-zero."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = CompletedProcess(
                args=[],
                returncode=1,
                stdout="",
                stderr="Error: the server returned an error",
            )
            result = dry_run_manifest(_SAMPLE_YAML, "minikube")
            assert result.is_safe is False

    def test_warnings_parsed_from_stderr(self) -> None:
        """Warnings from kubectl stderr are captured in the result."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"kind": "Deployment"}',
                stderr="Warning: resource Deployment/my-app is deprecated",
            )
            result = dry_run_manifest(_SAMPLE_YAML, "minikube")
            assert len(result.warnings) > 0
            assert any("deprecated" in w for w in result.warnings)

    def test_invalid_yaml_returns_error(self) -> None:
        """Invalid YAML is caught before calling kubectl."""
        result = dry_run_manifest("invalid: yaml: {{{{", "minikube")
        assert result.is_safe is False
        assert any("YAML" in w for w in result.warnings)

    def test_kubectl_not_found(self) -> None:
        """FileNotFoundError when kubectl is missing returns is_safe=False."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = dry_run_manifest(_SAMPLE_YAML, "minikube")
            assert result.is_safe is False
            assert any("kubectl not found" in w for w in result.warnings)

    def test_timeout_returns_unsafe(self) -> None:
        """Timeout returns is_safe=False with a descriptive warning."""
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="kubectl", timeout=30)):
            result = dry_run_manifest(_SAMPLE_YAML, "minikube")
            assert result.is_safe is False
            assert any("timed out" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# apply_manifest
# ---------------------------------------------------------------------------


class TestApplyManifest:
    """Tests for apply_manifest()."""

    def test_successful_apply(self) -> None:
        """apply_manifest returns success=True when kubectl exits 0."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = CompletedProcess(
                args=[],
                returncode=0,
                stdout="deployment.apps/my-app configured",
                stderr="",
            )
            result = apply_manifest(_SAMPLE_YAML, "minikube")
            assert result.success is True
            assert "my-app" in result.resource_name

    def test_failed_apply(self) -> None:
        """apply_manifest returns success=False when kubectl exits non-zero."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = CompletedProcess(
                args=[],
                returncode=1,
                stdout="",
                stderr="Error from server: deployments is forbidden",
            )
            result = apply_manifest(_SAMPLE_YAML, "minikube")
            assert result.success is False

    def test_kubectl_not_found_in_apply(self) -> None:
        """FileNotFoundError when kubectl is missing is handled gracefully."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = apply_manifest(_SAMPLE_YAML, "minikube")
            assert result.success is False


# ---------------------------------------------------------------------------
# generate_kubectl_command
# ---------------------------------------------------------------------------


class TestGenerateKubectlCommand:
    """Tests for generate_kubectl_command()."""

    def test_restart_deployment(self) -> None:
        """Restart intent generates a rollout restart command."""
        cmd = generate_kubectl_command(
            "restart the api-server deployment",
            {"kind": "deployment", "name": "api-server", "namespace": "production"},
        )
        assert "rollout restart" in cmd
        assert "api-server" in cmd

    def test_scale_deployment(self) -> None:
        """Scale intent generates a scale command."""
        cmd = generate_kubectl_command(
            "scale down to 3 replicas",
            {"kind": "deployment", "name": "web", "namespace": "default", "replicas": 3},
        )
        assert "scale" in cmd
        assert "3" in cmd

    def test_get_pods_fallback(self) -> None:
        """Unknown intent returns a kubectl get command."""
        cmd = generate_kubectl_command("show pods", {"kind": "pod", "namespace": "default"})
        assert "kubectl" in cmd
