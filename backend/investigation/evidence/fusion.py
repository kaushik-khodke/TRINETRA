"""
TRINETRA Phase 6 — Evidence Fusion Engine
Central synthesizer linking disparate evidence tokens into clusters, graph edges, and hypotheses.
"""

from typing import Dict, Any, List, Tuple, Optional
from investigation.evidence.models import EvidenceItem, EvidenceType
from investigation.evidence.relationships import EvidenceRelationship, RelationshipType
from investigation.evidence.graph import EvidenceGraph
from investigation.evidence.clustering import EvidenceClusterer, EvidenceCluster
from investigation.evidence.validator import EvidenceConflictValidator
from investigation.evidence.scoring import EvidenceScorer, ConfidenceBreakdown
from investigation.schemas import SemanticHypothesis, EvidenceConflict


class FusionResult:
    def __init__(
        self,
        evidence_count: int,
        graph: EvidenceGraph,
        clusters: List[Any],
        conflicts: List[Any],
        confidence: Any,
        relationships: Optional[List[Any]] = None,
    ):
        self.evidence_count = evidence_count
        self.graph = graph
        self.clusters = clusters
        self.conflicts = conflicts
        self.confidence = confidence
        self.relationships = relationships or (graph.get_edges() if graph else [])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_count": self.evidence_count,
            "clusters": [c.to_dict() if hasattr(c, "to_dict") else dict(c) for c in self.clusters],
            "conflicts": [c.to_dict() if hasattr(c, "to_dict") else dict(c) for c in self.conflicts],
            "relationships": [r.to_dict() if hasattr(r, "to_dict") else dict(r) for r in self.relationships],
            "confidence": self.confidence.to_dict() if hasattr(self.confidence, "to_dict") else self.confidence,
        }


class EvidenceFusionEngine:
    """
    Synthesizes multiple specialized analytical outputs into a unified relational evidence model.
    """

    @classmethod
    def fuse_evidence(
        cls,
        evidence_items: List[EvidenceItem],
        aoi_bounds: Optional[List[float]] = None,
        intent: str = "GENERAL_CHANGE",
    ) -> FusionResult:
        res = cls.fuse(evidence_items, intent=intent)
        return FusionResult(
            evidence_count=res["evidence_count"],
            graph=res["graph"],
            clusters=res["clusters"],
            conflicts=res["conflicts"],
            confidence=res["confidence"],
            relationships=res["graph"].get_edges(),
        )

    @classmethod
    def fuse(
        cls,
        evidence_items: List[EvidenceItem],
        intent: str = "GENERAL_CHANGE",
    ) -> Dict[str, Any]:
        graph = EvidenceGraph()
        for item in evidence_items:
            graph.add_node(item)

        # 1. Establish relationships
        cls._build_relationships(graph, evidence_items)

        # 2. Group into spatial/semantic clusters
        clusters = EvidenceClusterer.cluster(evidence_items)

        # 3. Detect contradictions and conflicts
        conflicts = EvidenceConflictValidator.find_conflicts(evidence_items)
        has_conflicts = len(conflicts) > 0

        # Mark conflict flag on affected clusters
        conflict_item_ids = set()
        for c in conflicts:
            conflict_item_ids.add(c.conflict_id)
        for cluster in clusters:
            if any(cid in cluster.evidence_ids for cid in conflict_item_ids):
                cluster.has_conflict = True

        # 4. Multi-dimensional confidence scoring
        confidence_breakdown = cls._calculate_confidence(evidence_items, has_conflicts)

        return {
            "evidence_count": len(evidence_items),
            "graph": graph,
            "clusters": clusters,
            "conflicts": conflicts,
            "confidence": confidence_breakdown,
        }

    @classmethod
    def _build_relationships(cls, graph: EvidenceGraph, items: List[EvidenceItem]) -> None:
        """Derives topological and corroborative edges between evidence tokens."""
        by_region: Dict[str, List[EvidenceItem]] = {}
        for item in items:
            rid = item.metadata.get("region_id")
            if rid:
                if rid not in by_region:
                    by_region[rid] = []
                by_region[rid].append(item)

        for rid, reg_items in by_region.items():
            for i in range(len(reg_items)):
                for j in range(i + 1, len(reg_items)):
                    a = reg_items[i]
                    b = reg_items[j]

                    # Same region link
                    graph.add_edge(
                        EvidenceRelationship(
                            source_id=a.id,
                            target_id=b.id,
                            relationship=RelationshipType.SAME_REGION,
                            weight=1.0,
                        )
                    )

        # Global pairwise analysis: Spatial Overlaps and Cross-Modal Corroboration
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a = items[i]
                b = items[j]

                # 1. Bounding box spatial overlap
                if a.bounding_box and b.bounding_box and len(a.bounding_box) >= 4 and len(b.bounding_box) >= 4:
                    min_x1, min_y1, max_x1, max_y1 = a.bounding_box[:4]
                    min_x2, min_y2, max_x2, max_y2 = b.bounding_box[:4]
                    overlaps = not (max_x1 < min_x2 or max_x2 < min_x1 or max_y1 < min_y2 or max_y2 < min_y1)
                    if overlaps:
                        graph.add_edge(
                            EvidenceRelationship(
                                source_id=a.id,
                                target_id=b.id,
                                relationship=RelationshipType.SPATIALLY_OVERLAPS,
                                weight=0.9,
                            )
                        )

                # 2. Corroboration: Optical Change + Grounding or Optical Change + Spectral
                if (a.type == EvidenceType.CHANGE and b.type in [EvidenceType.OBJECT, EvidenceType.SPECTRAL]) or \
                   (b.type == EvidenceType.CHANGE and a.type in [EvidenceType.OBJECT, EvidenceType.SPECTRAL]):
                    graph.add_edge(
                        EvidenceRelationship(
                            source_id=a.id,
                            target_id=b.id,
                            relationship=RelationshipType.CORROBORATES,
                            weight=0.85,
                        )
                    )

    @classmethod
    def _calculate_confidence(cls, items: List[EvidenceItem], has_conflicts: bool) -> ConfidenceBreakdown:
        if not items:
            return EvidenceScorer.evaluate(model_confidence=0.3, has_contradiction=has_conflicts)

        avg_model_conf = sum(it.confidence for it in items) / len(items)
        avg_quality = sum(it.quality for it in items) / len(items)

        has_sar = any(it.type == EvidenceType.SAR for it in items)
        has_opt = any(it.type == EvidenceType.OPTICAL or it.type == EvidenceType.CHANGE for it in items)
        cross_modal_score = 0.85 if (has_sar and has_opt and not has_conflicts) else 0.45

        return EvidenceScorer.evaluate(
            model_confidence=avg_model_conf,
            evidence_quality=avg_quality,
            spatial_support=0.8,
            temporal_support=0.75,
            cross_modal_support=cross_modal_score,
            data_quality=0.88,
            has_contradiction=has_conflicts,
        )
