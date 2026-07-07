"""The two-node LangGraph.

Exactly two nodes — Interview and Evaluation — with DETERMINISTIC routing (a plain
function reads ``state['mode']``; no LLM planner decides control flow). The graph is
compiled once and reused. If LangGraph is unavailable at runtime we fall back to
invoking the same node functions directly, so behavior is identical either way.
"""
from __future__ import annotations

from app.ai.nodes.evaluation_node import evaluation_node
from app.ai.nodes.interview_node import interview_node
from app.ai.state import InterviewState
from app.core.logging import get_logger

logger = get_logger("ai.graph")

_compiled = None


def _route(state: InterviewState) -> str:
    """Deterministic entry routing based on mode set by the service layer."""
    return "evaluation" if state.get("mode") == "evaluate" else "interview"


def _build_graph():
    from langgraph.graph import END, StateGraph

    graph = StateGraph(InterviewState)
    graph.add_node("interview", interview_node)
    graph.add_node("evaluation", evaluation_node)
    graph.set_conditional_entry_point(
        _route, {"interview": "interview", "evaluation": "evaluation"}
    )
    graph.add_edge("interview", END)
    graph.add_edge("evaluation", END)
    return graph.compile()


def get_graph():
    global _compiled
    if _compiled is None:
        try:
            _compiled = _build_graph()
            logger.info("LangGraph compiled (2 nodes: interview, evaluation).")
        except Exception as exc:  # noqa: BLE001
            logger.warning("LangGraph unavailable (%s); using direct node fallback.", exc)
            _compiled = _DirectFallback()
    return _compiled


class _DirectFallback:
    """Same contract as a compiled LangGraph app: ``await ainvoke(state)``."""

    async def ainvoke(self, state: InterviewState) -> InterviewState:
        if _route(state) == "evaluation":
            return await evaluation_node(state)
        return await interview_node(state)


async def run_graph(state: InterviewState) -> InterviewState:
    app = get_graph()
    return await app.ainvoke(state)
