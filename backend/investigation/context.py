"""
TRINETRA Phase 6 — Investigation Context
Decouples raw numerical state, raster windows, and evidence structures from prompt text.
"""

from typing import Dict, Any, List, Optional
import threading


class InvestigationContext:
    """
    Thread-safe raw numerical and structural context for an active investigation.
    """
    def __init__(
        self,
        investigation_id: str,
        question: str,
        aoi_geometry: Optional[Dict[str, Any]] = None,
        observation_ids: Optional[List[str]] = None,
    ):
        self.investigation_id = investigation_id
        self.question = question
        self.aoi_geometry = aoi_geometry
        self.observation_ids = observation_ids or []
        self.aoi_bounds: Optional[List[float]] = None
        self.tensors: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        self.evidence_items: List[Any] = []
        self.evidence_relationships: List[Any] = []
        self.evidence_clusters: List[Any] = []
        self.hypotheses: List[Any] = []
        self.findings: List[Any] = []
        self.conflicts: List[Any] = []
        self.limitations: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def add_evidence(self, item: Any) -> None:
        with self._lock:
            self.evidence_items.append(item)

    def add_relationship(self, rel: Any) -> None:
        with self._lock:
            self.evidence_relationships.append(rel)

    def add_limitation(self, code: str, message: str, severity: str = "medium", impact: str = "") -> None:
        with self._lock:
            self.limitations.append({
                "code": code,
                "message": message,
                "severity": severity,
                "impact": impact,
            })

    def get_evidence_by_id(self, eid: str) -> Optional[Any]:
        with self._lock:
            for item in self.evidence_items:
                if hasattr(item, "id") and item.id == eid:
                    return item
                if isinstance(item, dict) and item.get("id") == eid:
                    return item
            return None
