"""
LangGraph node function implementations.

Each function in this module corresponds to a node in the StateGraph.
Nodes receive the full KubeNovaState, perform their work, and return a
partial dict that LangGraph merges back into the state.
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from loguru import logger

from app.core.agents.state import KubeNovaState
from app.core.k8s.executor import RiskLevel, classify_intent_risk
from app.core.llm.factory import get_llm_provider

_SYSTEM_PROMPT = """You are KubeNova, an expert Kubernetes assistant embedded in a
production cluster management interface. You help operators understand their cluster,
diagnose incidents, and safely apply changes.

Guidelines:
- Always verify the current state of resources before suggesting changes.
- For any destructive operation, explain what will happen and what the impact is.
- Prefer the least-privilege approach: read before write.
- When you generate a kubectl command or manifest, the system will run a dry-run
  validation and show the user a preview before applying anything.
- Be concise and precise. Operators are busy.
- If you're not sure about something, say so — don't invent API behaviour.
"""


def intent_classifier_node(state: KubeNovaState) -> dict[str, Any]:
    """
    Extract the user's intent from the latest message and classify its risk.

    This is the first node in the graph. It reads the last HumanMessage,
    stores the raw text as user_intent, and computes the initial risk_level.

    Args:
        state: Current graph state.

    Returns:
        Partial state update with user_intent and risk_level.
    """
    messages = state.get("messages", [])
    user_intent = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_intent = str(msg.content)
            break

    risk = classify_intent_risk(user_intent)
    logger.info("Intent classified: risk={} intent='{}'", risk.value, user_intent[:80])
    return {
        "user_intent": user_intent,
        "risk_level": risk.value,
    }


def safety_gate_node(state: KubeNovaState) -> dict[str, Any]:
    """
    Safety gate that blocks CRITICAL operations before any tool is called.

    For CRITICAL risk, this node sets an error message and the graph routes
    to the blocked_node. For all other risk levels, it passes through unchanged.

    Args:
        state: Current graph state.

    Returns:
        Partial state update (may set error for CRITICAL).
    """
    risk = state.get("risk_level", RiskLevel.LOW.value)
    if risk == RiskLevel.CRITICAL.value:
        error_msg = (
            "This operation has been blocked because it is classified as CRITICAL risk. "
            "KubeNova does not automate: namespace deletion, node deletion, node draining, "
            "or bulk --all deletes. Please perform this operation manually with full awareness "
            "of the consequences."
        )
        logger.warning("Safety gate BLOCKED critical operation: {}", state.get("user_intent", "")[:80])
        return {"error": error_msg}
    return {"risk_level": risk}


def executor_node(state: KubeNovaState) -> dict[str, Any]:
    """
    Call the LLM with all tools available and accumulate tool call results.

    This node binds the registered tools to the chat model and invokes it.
    If the model returns tool calls, they are executed and results appended.
    This continues until the model produces a final AIMessage without tool calls.

    Args:
        state: Current graph state.

    Returns:
        Partial state update with updated messages list.
    """
    from app.core.agents.tools import ALL_TOOLS
    from langchain_core.messages import ToolMessage as LCToolMessage

    provider = get_llm_provider()
    llm = provider.get_chat_model()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)  # type: ignore[attr-defined]

    messages: list[Any] = list(state.get("messages", []))
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=_SYSTEM_PROMPT)] + messages

    # Tool call loop — continue until no more tool calls.
    max_iterations = 10
    for _ in range(max_iterations):
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        tool_calls = getattr(response, "tool_calls", [])
        if not tool_calls:
            break

        # Execute each tool call.
        tool_map = {t.name: t for t in ALL_TOOLS}
        for tc in tool_calls:
            tool_name = tc["name"]
            tool_args = tc["args"]
            tool_id = tc["id"]

            tool_fn = tool_map.get(tool_name)
            if tool_fn is None:
                result = f"Error: unknown tool '{tool_name}'"
            else:
                try:
                    result = tool_fn.invoke(tool_args)
                except Exception as exc:
                    result = f"Tool error: {exc}"

            messages.append(
                LCToolMessage(content=str(result), tool_call_id=tool_id)
            )

    return {"messages": messages}


def responder_node(state: KubeNovaState) -> dict[str, Any]:
    """
    Format the final response for the frontend.

    Reads the last AIMessage from the state, extracts any embedded command
    preview, and packages everything for the API response layer.

    Args:
        state: Current graph state.

    Returns:
        Partial state update (no-op here — response is in messages).
    """
    messages = state.get("messages", [])
    last_ai = None
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            last_ai = msg
            break

    if last_ai is None:
        logger.warning("responder_node: no AIMessage found in state.")

    return {"error": state.get("error")}


def human_review_node(state: KubeNovaState) -> dict[str, Any]:
    """
    Pause point for HIGH-risk operations requiring explicit user approval.

    In the WebSocket flow, the frontend is sent a `command_preview` chunk
    and must reply with an approval before execution continues.
    This node records that approval is required.

    Args:
        state: Current graph state.

    Returns:
        Partial state update marking command_preview as pending approval.
    """
    logger.info("HIGH-risk operation requires user approval.")
    return {"user_approved": False}


def blocked_node(state: KubeNovaState) -> dict[str, Any]:
    """
    Terminal node for CRITICAL-risk operations.

    Appends a blocking AIMessage to the conversation so the frontend can
    display the refusal to the user.

    Args:
        state: Current graph state.

    Returns:
        Partial state update with blocking AIMessage appended.
    """
    error = state.get("error", "Operation blocked.")
    messages = list(state.get("messages", []))
    messages.append(AIMessage(content=f"🚫 {error}"))
    return {"messages": messages}


def incident_analyzer_node(state: KubeNovaState) -> dict[str, Any]:
    """
    Guided incident response analysis node.

    Systematically queries cluster state (events, pod logs, node conditions)
    and accumulates findings. The LLM synthesises probable root causes from
    the findings list before handing off to responder_node.

    Args:
        state: Current graph state.

    Returns:
        Partial state update with incident_findings populated.
    """
    from app.core.k8s.resources import resource_fetcher

    cluster_context = state.get("cluster_context", "")
    namespace = state.get("namespace", "default")
    findings: list[str] = []

    # 1. Check for failing pods.
    pods = resource_fetcher.list_pods(namespace=namespace, cluster_context=cluster_context)
    crashing = [p for p in pods if "CrashLoopBackOff" in p.status or p.status == "Failed"]
    if crashing:
        findings.append(
            f"Found {len(crashing)} crashing pod(s): "
            + ", ".join(p.name for p in crashing)
        )

    pending = [p for p in pods if p.status == "Pending"]
    if pending:
        findings.append(
            f"Found {len(pending)} pending pod(s): "
            + ", ".join(p.name for p in pending)
        )

    # 2. Check recent Warning events.
    events = resource_fetcher.list_events(namespace=namespace, cluster_context=cluster_context)
    warnings = [e for e in events[:20] if e.type == "Warning"]
    if warnings:
        findings.append(
            f"Recent warning events ({len(warnings)}): "
            + "; ".join(f"{e.reason}: {e.message[:80]}" for e in warnings[:5])
        )

    # 3. Check node pressure.
    nodes = resource_fetcher.list_nodes(cluster_context=cluster_context)
    for node in nodes:
        for cond in node.conditions:
            if cond.type in ("MemoryPressure", "DiskPressure", "PIDPressure") and cond.status == "True":
                findings.append(f"Node '{node.name}' has condition {cond.type}=True.")

    if not findings:
        findings.append("No obvious issues detected. Cluster appears healthy.")

    # Build a synthesis prompt for the responder.
    messages = list(state.get("messages", []))
    findings_text = "\n".join(f"- {f}" for f in findings)
    messages.append(
        HumanMessage(
            content=(
                f"Incident analysis findings:\n{findings_text}\n\n"
                "Based on these findings, provide a structured incident report with:\n"
                "1. Summary of the issue\n"
                "2. Probable root causes\n"
                "3. Recommended remediation steps"
            )
        )
    )

    logger.info("Incident analyzer found {} findings.", len(findings))
    return {
        "incident_findings": findings,
        "messages": messages,
    }
