"""
TRINETRA Analysis Engine — StateGraph TypedDict
Maintains raw, typed state across all LangGraph execution nodes.
"""

from typing import TypedDict, Optional, List, Dict, Any


class AnalysisGraphState(TypedDict, total=False):
    # Request & Configuration
    run_id: str
    request_id: str
    query: str
    mode: str
    task: str
    aoi_geometry: Optional[Dict[str, Any]]
    aoi_bounds: Optional[List[float]]
    options: Dict[str, Any]

    # Observations & Assets
    observation_ids: List[str]
    resolved_observations: List[Dict[str, Any]]
    asset_paths: Dict[str, str]

    # Preprocessed In-memory References
    tensors: Dict[str, Any]
    validity_mask: Any
    preprocessing_meta: Dict[str, Any]

    # Specialist Results & Evidence
    specialist_out: Dict[str, Any]
    evidence_pack: Optional[Dict[str, Any]]
    evidence_valid: bool

    # Reasoning & Synthesis
    narrative: Optional[Dict[str, Any]]
    limitations: List[Dict[str, Any]]

    # Final Output
    provenance_manifest: Optional[Dict[str, Any]]
    artifacts: List[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    error: Optional[Dict[str, Any]]
