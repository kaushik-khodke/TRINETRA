"""
TRINETRA Analysis Engine — LangGraph StateGraph Workflow
Compiles the Explore-specific Earth Observation Analysis Graph.
"""

from langgraph.graph import StateGraph, END
from analysis_engine.graph.state import AnalysisGraphState
from analysis_engine.graph.nodes import (
    validate_request_node,
    resolve_observations_node,
    prepare_assets_node,
    preprocess_node,
    run_change_analysis_node,
    run_sar_optical_node,
    run_single_image_node,
    validate_evidence_node,
    reasoning_node,
    generate_report_node,
)
from analysis_engine.graph.routing import route_analysis_mode


def build_analysis_graph():
    """
    Constructs and compiles the Explore Analysis LangGraph.
    """
    workflow = StateGraph(AnalysisGraphState)

    # 1. Register Nodes
    workflow.add_node("validate_request", validate_request_node)
    workflow.add_node("resolve_observations", resolve_observations_node)
    workflow.add_node("prepare_assets", prepare_assets_node)
    workflow.add_node("preprocess", preprocess_node)

    workflow.add_node("run_change_analysis", run_change_analysis_node)
    workflow.add_node("run_sar_optical", run_sar_optical_node)
    workflow.add_node("run_single_image", run_single_image_node)

    workflow.add_node("validate_evidence", validate_evidence_node)
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("generate_report", generate_report_node)

    # 2. Linear Pre-analysis Edges
    workflow.set_entry_point("validate_request")
    workflow.add_edge("validate_request", "resolve_observations")
    workflow.add_edge("resolve_observations", "prepare_assets")
    workflow.add_edge("prepare_assets", "preprocess")

    # 3. Conditional Mode Branching
    workflow.add_conditional_edges(
        "preprocess",
        route_analysis_mode,
        {
            "run_change_analysis": "run_change_analysis",
            "run_sar_optical": "run_sar_optical",
            "run_single_image": "run_single_image",
            "error": END,
        },
    )

    # 4. Convergence onto Evidence & Reasoning
    workflow.add_edge("run_change_analysis", "validate_evidence")
    workflow.add_edge("run_sar_optical", "validate_evidence")
    workflow.add_edge("run_single_image", "validate_evidence")

    workflow.add_edge("validate_evidence", "reasoning")
    workflow.add_edge("reasoning", "generate_report")
    workflow.add_edge("generate_report", END)

    return workflow.compile()


# Global compiled graph instance
analysis_graph = build_analysis_graph()
