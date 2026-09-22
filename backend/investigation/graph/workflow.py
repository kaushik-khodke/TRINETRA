"""
TRINETRA Phase 6 — Investigation LangGraph Workflow Definition
Compiles the deterministic multi-specialist evidence fusion and reasoning graph.
"""

from langgraph.graph import StateGraph, END
from investigation.graph.state import InvestigationGraphState
from investigation.graph.nodes import (
    plan_investigation_node,
    execute_specialists_node,
    fuse_evidence_node,
    classify_semantics_node,
    reason_conclusion_node,
    compile_report_node,
)
from investigation.graph.routing import route_after_planning, route_after_execution


def build_investigation_graph():
    """
    Constructs and compiles the Phase 6 Investigation LangGraph.
    """
    workflow = StateGraph(InvestigationGraphState)

    # 1. Register Nodes
    workflow.add_node("plan_investigation", plan_investigation_node)
    workflow.add_node("execute_specialists", execute_specialists_node)
    workflow.add_node("fuse_evidence", fuse_evidence_node)
    workflow.add_node("classify_semantics", classify_semantics_node)
    workflow.add_node("reason_conclusion", reason_conclusion_node)
    workflow.add_node("compile_report", compile_report_node)

    # 2. Wire Entry Point & Conditional Branching
    workflow.set_entry_point("plan_investigation")

    workflow.add_conditional_edges(
        "plan_investigation",
        route_after_planning,
        {
            "execute_specialists": "execute_specialists",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        "execute_specialists",
        route_after_execution,
        {
            "fuse_evidence": "fuse_evidence",
            "reason_conclusion": "reason_conclusion",
        },
    )

    # 3. Downstream Sequential Edges
    workflow.add_edge("fuse_evidence", "classify_semantics")
    workflow.add_edge("classify_semantics", "reason_conclusion")
    workflow.add_edge("reason_conclusion", "compile_report")
    workflow.add_edge("compile_report", END)

    return workflow.compile()


# Global compiled instance
investigation_graph = build_investigation_graph()
