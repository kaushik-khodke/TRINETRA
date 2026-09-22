"""
TRINETRA Phase 6 — Investigation LangGraph State Schema
Typed state dictionary threaded across all nodes of the investigation graph.
"""

from typing import TypedDict, Dict, Any, List, Optional


class InvestigationGraphState(TypedDict, total=False):
    investigation_id: str
    question: str
    observation_ids: List[str]
    aoi: Optional[Dict[str, Any]]
    status: str
    plan: Dict[str, Any]
    context: Any  # InvestigationContext reference
    evidence_items: List[Dict[str, Any]]
    evidence_relationships: List[Dict[str, Any]]
    evidence_clusters: List[Dict[str, Any]]
    conflicts: List[Dict[str, Any]]
    findings: List[Dict[str, Any]]
    hypotheses: List[Dict[str, Any]]
    conclusion: Dict[str, Any]
    artifacts: List[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]
    limitations: List[Dict[str, Any]]
