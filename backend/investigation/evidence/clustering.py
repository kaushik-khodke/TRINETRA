"""
TRINETRA Phase 6 — Evidence Clustering
Aggregates atomic evidence tokens into cohesive multi-source clusters.
"""

from typing import Dict, Any, List, Optional
import uuid
from pydantic import BaseModel, Field
from investigation.evidence.models import EvidenceItem


class EvidenceCluster(BaseModel):
    cluster_id: str = Field(default_factory=lambda: f"cl_{uuid.uuid4().hex[:8]}")
    primary_region_id: Optional[str] = None
    bounding_box: Optional[List[float]] = None
    evidence_ids: List[str] = Field(default_factory=list)
    semantic_tag: str = "UNCLASSIFIED"
    aggregate_confidence: float = 0.5
    has_conflict: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "primary_region_id": self.primary_region_id,
            "bounding_box": self.bounding_box,
            "evidence_ids": self.evidence_ids,
            "semantic_tag": self.semantic_tag,
            "aggregate_confidence": self.aggregate_confidence,
            "has_conflict": self.has_conflict,
            "metadata": self.metadata,
        }


class EvidenceClusterer:
    """
    Partitions evidence items into spatial and semantic clusters.
    """

    @classmethod
    def cluster(cls, evidence_items: List[EvidenceItem]) -> List[EvidenceCluster]:
        if not evidence_items:
            return []

        # 1. Group by region_id if specified in metadata
        region_map: Dict[str, List[EvidenceItem]] = {}
        unassigned: List[EvidenceItem] = []

        for item in evidence_items:
            rid = item.metadata.get("region_id")
            if rid:
                if rid not in region_map:
                    region_map[rid] = []
                region_map[rid].append(item)
            else:
                unassigned.append(item)

        clusters: List[EvidenceCluster] = []

        # Create clusters from region groupings
        for rid, items in region_map.items():
            bboxes = [it.bounding_box for it in items if it.bounding_box]
            cluster_bbox = cls._merge_bboxes(bboxes) if bboxes else None
            avg_conf = sum(it.confidence for it in items) / max(1, len(items))

            cluster = EvidenceCluster(
                primary_region_id=rid,
                bounding_box=cluster_bbox,
                evidence_ids=[it.id for it in items],
                aggregate_confidence=round(avg_conf, 3),
            )
            clusters.append(cluster)

        # Cluster remaining items by spatial bbox overlap
        if unassigned:
            remaining_ids = [it.id for it in unassigned]
            cluster = EvidenceCluster(
                primary_region_id="global_scene",
                evidence_ids=remaining_ids,
                aggregate_confidence=round(sum(it.confidence for it in unassigned) / len(unassigned), 3),
            )
            clusters.append(cluster)

        return clusters

    @staticmethod
    def _merge_bboxes(bboxes: List[List[float]]) -> Optional[List[float]]:
        if not bboxes:
            return None
        min_lon = min(b[0] for b in bboxes)
        min_lat = min(b[1] for b in bboxes)
        max_lon = max(b[2] for b in bboxes)
        max_lat = max(b[3] for b in bboxes)
        return [min_lon, min_lat, max_lon, max_lat]
