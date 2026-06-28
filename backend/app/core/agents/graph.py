"""
LangGraph StateGraph definition for the KubeNova agent.

The graph wires together all node functions with conditional routing based
on the risk_level and incident_mode fields in the shared state.

Exported symbol: ``compiled_graph`` — a pre-compiled LangGraph runnable
that can be invoked or streamed by the API layer.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph  # type: ignore[import]

from app.core.agents.nodes import (
    blocked_node,
    executor_node,
    human_review_node,
    incident_analyzer_node,
    intent_classifier_node,
    responder_node,
    safety_gate_node,
)
from app.core.agents.state import KubeNovaState
from app.core.k8s.executor import RiskLevel


def _route_after_safety_gate(state: KubeNovaState) -> str:
    """
    Conditional edge function: decides where to go after safety_gate_node.

    Routing rules:
    - CRITICAL risk → blocked_node (terminal refusal)
    - incident_mode=True → incident_analyzer_node
    - HIGH risk → human_review_node (approval required)
    - LOW / MEDIUM → executor_node directly

    Args:
        state: Current graph state after safety_gate_node ran.

    Returns:
        Name of the next node to execute.
    """
    if state.get("error"):
        return "blocked"

    if state.get("incident_mode", False):
        return "incident_analyzer"

    risk = state.get("risk_level", RiskLevel.LOW.value)
    if risk == RiskLevel.HIGH.value:
        return "human_review"

    return "executor"


def _route_after_human_review(state: KubeNovaState) -> str:
    """
    Conditional edge: proceed to executor only if user has approved.

    Args:
        state: Current graph state.

    Returns:
        'executor' if approved, 'blocked' otherwise.
    """
    if state.get("user_approved", False):
        return "executor"
    # If not yet approved the graph pauses — the WebSocket handler will
    # re-invoke the graph once the approval message arrives.
    return "blocked"


def build_graph() -> Any:
    """
    Construct and compile the KubeNova StateGraph.

    Returns:
        A compiled LangGraph runnable (CompiledStateGraph).
    """
    graph = StateGraph(KubeNovaState)

    # Register all nodes.
    graph.add_node("intent_classifier", intent_classifier_node)
    graph.add_node("safety_gate", safety_gate_node)
    graph.add_node("executor", executor_node)
    graph.add_node("responder", responder_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("blocked", blocked_node)
    graph.add_node("incident_analyzer", incident_analyzer_node)

    # Entry point.
    graph.set_entry_point("intent_classifier")

    # Fixed edges.
    graph.add_edge("intent_classifier", "safety_gate")

    # Conditional routing after safety gate.
    graph.add_conditional_edges(
        "safety_gate",
        _route_after_safety_gate,
        {
            "executor": "executor",
            "human_review": "human_review",
            "blocked": "blocked",
            "incident_analyzer": "incident_analyzer",
        },
    )

    # Human review → executor or blocked.
    graph.add_conditional_edges(
        "human_review",
        _route_after_human_review,
        {
            "executor": "executor",
            "blocked": "blocked",
        },
    )

    # Incident analyzer flows into executor for final synthesis.
    graph.add_edge("incident_analyzer", "executor")

    # Executor always flows to responder.
    graph.add_edge("executor", "responder")

    # Terminal nodes.
    graph.add_edge("responder", END)
    graph.add_edge("blocked", END)

    return graph.compile()


# Module-level compiled graph — imported by the API routes.
compiled_graph = build_graph()
