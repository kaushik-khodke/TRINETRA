"""
TRINETRA Phase 6 — Investigation Workflow Routing
Conditional branching logic based on planning validation and specialist outcomes.
"""

from langgraph.graph import END
from investigation.graph.state import InvestigationGraphState


def route_after_planning(state: InvestigationGraphState) -> str:
    """Routes to specialist execution or ends if validation failed."""
    if state.get("errors"):
        return END
    return "execute_specialists"


def route_after_execution(state: InvestigationGraphState) -> str:
    """Routes to fusion, or straight to reasoning if no evidence gathered."""
    items = state.get("evidence_items", [])
    if not items:
        return "reason_conclusion"
    return "fuse_evidence"
