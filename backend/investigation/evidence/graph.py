"""
TRINETRA Phase 6 — Evidence Graph
Directed graph modeling nodes (EvidenceItem) and typed edges (EvidenceRelationship).
"""

from typing import Dict, Any, List, Optional
from investigation.evidence.models import EvidenceItem
from investigation.evidence.relationships import EvidenceRelationship, RelationshipType


class EvidenceGraph:
    """
    In-memory graph of evidence nodes and relational edges.
    """
    def __init__(self):
        self._nodes: Dict[str, EvidenceItem] = {}
        self._edges: List[EvidenceRelationship] = []
        self._adj: Dict[str, List[EvidenceRelationship]] = {}

    def add_node(self, item: EvidenceItem) -> None:
        self._nodes[item.id] = item
        if item.id not in self._adj:
            self._adj[item.id] = []

    def add_edge(self, edge: EvidenceRelationship) -> None:
        if edge.source_id not in self._nodes or edge.target_id not in self._nodes:
            return
        self._edges.append(edge)
        self._adj[edge.source_id].append(edge)

    def get_node(self, node_id: str) -> Optional[EvidenceItem]:
        return self._nodes.get(node_id)

    def get_edges(self) -> List[EvidenceRelationship]:
        return list(self._edges)

    def get_neighbors(self, node_id: str) -> List[EvidenceItem]:
        neighbors = []
        for edge in self._adj.get(node_id, []):
            if edge.target_id in self._nodes:
                neighbors.append(self._nodes[edge.target_id])
        return neighbors

    def find_relationships(self, rel_type: RelationshipType) -> List[EvidenceRelationship]:
        return [e for e in self._edges if e.relationship == rel_type]

    def to_dict(self) -> Dict[str, Any]:
        """Serializes graph to a D3/Cytoscape compatible JSON structure."""
        return {
            "nodes": [
                {
                    "id": item.id,
                    "type": item.type.value if hasattr(item.type, "value") else str(item.type),
                    "source": item.source,
                    "confidence": item.confidence,
                    "value": str(item.value)[:60] if item.value is not None else "",
                    "bounding_box": item.bounding_box,
                }
                for item in self._nodes.values()
            ],
            "edges": [e.to_dict() for e in self._edges],
            "node_count": len(self._nodes),
            "edge_count": len(self._edges),
        }
