"""
Kubernetes command executor with dry-run safety gate.

All destructive operations must pass through dry_run_manifest() before
apply_manifest() may be called. classify_intent_risk() provides fast
risk assessment used by the LangGraph safety_gate node.
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import tempfile
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from loguru import logger
from pydantic import BaseModel

from app.config import get_settings


class RiskLevel(str, Enum):
    """Four-tier risk classification for cluster operations."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DryRunResult(BaseModel):
    """Output of a kubectl --dry-run=server invocation."""

    is_safe: bool
    diff: str
    warnings: list[str]
    resource_name: str
    resource_kind: str
    raw_output: str = ""


class ApplyResult(BaseModel):
    """Output of a kubectl apply invocation."""

    success: bool
    resource_name: str
    resource_kind: str
    message: str
    events: list[str] = []


_CRITICAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bdelete\b.*\bnamespace\b", re.IGNORECASE),
    re.compile(r"\bdelete\b.*\bnode\b", re.IGNORECASE),
    re.compile(r"\bdrain\b.*\bnode\b", re.IGNORECASE),
    re.compile(r"\bdelete\b.*--all\b", re.IGNORECASE),
    re.compile(r"\bdelete\b.*\bcluster\b", re.IGNORECASE),
]

_HIGH_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bscale\b.*--replicas=0\b", re.IGNORECASE),
    re.compile(r"\bscale\b.*\s0\b", re.IGNORECASE),
    re.compile(r"\bdelete\b.*\b(deployment|statefulset|daemonset)\b", re.IGNORECASE),
    re.compile(r"\bexec\b.*-it?\b", re.IGNORECASE),
    re.compile(r"\bexec\b", re.IGNORECASE),
    re.compile(r"\bdelete\b.*\b(secret|configmap)\b", re.IGNORECASE),
]

_LOW_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^\s*(get|describe|logs|events|top|version|explain)\b", re.IGNORECASE),
]


def classify_intent_risk(command_text: str) -> RiskLevel:
    """
    Classify the risk level of a natural language intent or kubectl command.

    The function checks patterns in order from most to least severe.

    Args:
        command_text: Raw user intent or generated kubectl command string.

    Returns:
        RiskLevel enum value.
    """
    for pattern in _CRITICAL_PATTERNS:
        if pattern.search(command_text):
            logger.warning("CRITICAL risk detected in: {}", command_text[:120])
            return RiskLevel.CRITICAL

    for pattern in _HIGH_PATTERNS:
        if pattern.search(command_text):
            logger.info("HIGH risk detected in: {}", command_text[:120])
            return RiskLevel.HIGH

    for pattern in _LOW_PATTERNS:
        if pattern.match(command_text):
            return RiskLevel.LOW

    # Default: any write operation that didn't match the above is MEDIUM.
    write_keywords = re.compile(
        r"\b(apply|create|patch|replace|annotate|label|rollout|set|taint)\b",
        re.IGNORECASE,
    )
    if write_keywords.search(command_text):
        return RiskLevel.MEDIUM

    return RiskLevel.LOW


def _build_kubeconfig_args(cluster_context: str) -> list[str]:
    """Return kubectl flags for context and optional kubeconfig path."""
    settings = get_settings()
    args = ["--context", cluster_context]
    if settings.KUBECONFIG_PATH:
        args = ["--kubeconfig", settings.KUBECONFIG_PATH] + args
    return args


def dry_run_manifest(manifest_yaml: str, cluster_context: str) -> DryRunResult:
    """
    Validate a YAML manifest using kubectl apply --dry-run=server.

    Parses the YAML to extract resource metadata, then invokes kubectl
    in a subprocess. Captures stdout (JSON diff) and stderr (warnings).

    Args:
        manifest_yaml: Raw YAML string of the Kubernetes manifest.
        cluster_context: kubeconfig context to target.

    Returns:
        DryRunResult with safety assessment and diff output.
    """
    # Parse YAML to extract resource metadata before running kubectl.
    try:
        manifest_dict: dict[str, Any] = yaml.safe_load(manifest_yaml) or {}
    except yaml.YAMLError as exc:
        return DryRunResult(
            is_safe=False,
            diff="",
            warnings=[f"YAML parse error: {exc}"],
            resource_name="unknown",
            resource_kind="unknown",
        )

    resource_kind = manifest_dict.get("kind", "unknown")
    metadata = manifest_dict.get("metadata", {})
    resource_name = metadata.get("name", "unknown")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as tmp:
        tmp.write(manifest_yaml)
        tmp_path = Path(tmp.name)

    try:
        cmd = (
            ["kubectl"]
            + _build_kubeconfig_args(cluster_context)
            + [
                "apply",
                "--dry-run=server",
                "-o",
                "json",
                "-f",
                str(tmp_path),
            ]
        )
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )

        warnings: list[str] = []
        for line in result.stderr.splitlines():
            line = line.strip()
            if line:
                warnings.append(line)

        is_safe = result.returncode == 0
        diff_output = result.stdout if is_safe else result.stderr

        # Attempt to produce a human-readable diff from the JSON output.
        diff_str = _format_diff(diff_output, resource_kind, resource_name)

        return DryRunResult(
            is_safe=is_safe,
            diff=diff_str,
            warnings=warnings,
            resource_name=resource_name,
            resource_kind=resource_kind,
            raw_output=result.stdout,
        )
    except subprocess.TimeoutExpired:
        return DryRunResult(
            is_safe=False,
            diff="",
            warnings=["kubectl dry-run timed out after 30 seconds."],
            resource_name=resource_name,
            resource_kind=resource_kind,
        )
    except FileNotFoundError:
        return DryRunResult(
            is_safe=False,
            diff="",
            warnings=["kubectl not found in PATH. Cannot perform dry-run validation."],
            resource_name=resource_name,
            resource_kind=resource_kind,
        )
    finally:
        tmp_path.unlink(missing_ok=True)


def _format_diff(raw: str, kind: str, name: str) -> str:
    """Format kubectl dry-run output into a unified diff-like string."""
    try:
        parsed = json.loads(raw)
        return f"# Dry-run: {kind}/{name}\n" + json.dumps(parsed, indent=2)
    except (json.JSONDecodeError, ValueError):
        return raw or f"# Dry-run: {kind}/{name} — no diff output"


def apply_manifest(manifest_yaml: str, cluster_context: str) -> ApplyResult:
    """
    Apply a YAML manifest to the cluster.

    This method should only be called after dry_run_manifest() has been
    run and the user has explicitly approved the operation.

    Args:
        manifest_yaml: Raw YAML string of the Kubernetes manifest.
        cluster_context: kubeconfig context to target.

    Returns:
        ApplyResult with success flag and resource reference.
    """
    try:
        manifest_dict: dict[str, Any] = yaml.safe_load(manifest_yaml) or {}
    except yaml.YAMLError as exc:
        return ApplyResult(
            success=False,
            resource_name="unknown",
            resource_kind="unknown",
            message=f"YAML parse error: {exc}",
        )

    resource_kind = manifest_dict.get("kind", "unknown")
    resource_name = manifest_dict.get("metadata", {}).get("name", "unknown")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as tmp:
        tmp.write(manifest_yaml)
        tmp_path = Path(tmp.name)

    try:
        cmd = (
            ["kubectl"]
            + _build_kubeconfig_args(cluster_context)
            + ["apply", "-f", str(tmp_path)]
        )
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        success = result.returncode == 0
        message = result.stdout.strip() if success else result.stderr.strip()
        logger.info(
            "kubectl apply {} for {}/{}: {}",
            "succeeded" if success else "failed",
            resource_kind,
            resource_name,
            message[:200],
        )
        return ApplyResult(
            success=success,
            resource_name=resource_name,
            resource_kind=resource_kind,
            message=message,
        )
    except subprocess.TimeoutExpired:
        return ApplyResult(
            success=False,
            resource_name=resource_name,
            resource_kind=resource_kind,
            message="kubectl apply timed out after 60 seconds.",
        )
    except FileNotFoundError:
        return ApplyResult(
            success=False,
            resource_name=resource_name,
            resource_kind=resource_kind,
            message="kubectl not found in PATH.",
        )
    finally:
        tmp_path.unlink(missing_ok=True)


def generate_kubectl_command(intent: str, resources: dict[str, Any]) -> str:
    """
    Generate a kubectl command string from an intent description.

    This function produces the command string only — it does NOT execute it.
    The returned string is embedded in the AI's response for display.

    Args:
        intent: Natural language intent (e.g. "restart the api-server deployment").
        resources: Contextual resource info (namespace, name, kind, etc.).

    Returns:
        A kubectl command string ready to display to the user.
    """
    namespace = resources.get("namespace", "default")
    name = resources.get("name", "")
    kind = resources.get("kind", "").lower()

    intent_lower = intent.lower()

    if "restart" in intent_lower and kind in ("deployment", "statefulset", "daemonset"):
        return f"kubectl rollout restart {kind}/{name} -n {namespace}"

    if "scale" in intent_lower:
        replicas = resources.get("replicas", 1)
        return f"kubectl scale {kind}/{name} --replicas={replicas} -n {namespace}"

    if "delete" in intent_lower:
        return f"kubectl delete {kind}/{name} -n {namespace}"

    if "describe" in intent_lower:
        return f"kubectl describe {kind}/{name} -n {namespace}"

    if "logs" in intent_lower:
        container = resources.get("container", "")
        container_flag = f" -c {container}" if container else ""
        return f"kubectl logs {name}{container_flag} -n {namespace} --tail=100"

    if "get" in intent_lower:
        return f"kubectl get {kind} -n {namespace}"

    # Generic fallback.
    return f"kubectl get {kind} {name} -n {namespace}".strip()


def execute_kubectl_command(command_str: str, cluster_context: str) -> ApplyResult:
    """
    Execute a raw kubectl command string securely by injecting the cluster context.

    Args:
        command_str: The generated kubectl command string to execute.
        cluster_context: The kubeconfig context name to target.

    Returns:
        ApplyResult with success flag and CLI stdout/stderr.
    """
    if not command_str.strip().startswith("kubectl"):
        return ApplyResult(
            success=False,
            resource_name="unknown",
            resource_kind="unknown",
            message=f"Invalid command string (must start with kubectl): {command_str}",
        )

    args = shlex.split(command_str)
    # Strip the leading 'kubectl'
    args = args[1:]

    # Remove any --context flag to avoid duplicate context arguments
    filtered_args = []
    skip = False
    for arg in args:
        if skip:
            skip = False
            continue
        if arg == "--context":
            skip = True
            continue
        if arg.startswith("--context="):
            continue
        filtered_args.append(arg)

    cmd = (
        ["kubectl"]
        + _build_kubeconfig_args(cluster_context)
        + filtered_args
    )

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        success = result.returncode == 0
        message = result.stdout.strip() if success else result.stderr.strip()
        logger.info(
            "kubectl command execution {}: {}",
            "succeeded" if success else "failed",
            message[:200],
        )
        return ApplyResult(
            success=success,
            resource_name="unknown",
            resource_kind="unknown",
            message=message,
        )
    except subprocess.TimeoutExpired:
        return ApplyResult(
            success=False,
            resource_name="unknown",
            resource_kind="unknown",
            message="kubectl command timed out after 60 seconds.",
        )
    except FileNotFoundError:
        return ApplyResult(
            success=False,
            resource_name="unknown",
            resource_kind="unknown",
            message="kubectl not found in PATH.",
        )
