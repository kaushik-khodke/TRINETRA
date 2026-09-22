"""
TRINETRA Phase 7 — Multi-Dimensional Search Ranking
Scores search candidate relevance and generates transparent, auditable match reasons.
"""

from typing import Dict, Any, List, Tuple, Optional
from intelligence.models import EOEvent, PersistentFinding
from intelligence.events.matcher import compute_bbox_iou


class SearchRanker:
    """
    Ranks search results across orthogonal dimensions with explainable match rationales.
    """

    @classmethod
    def score_event(
        cls,
        event: EOEvent,
        parsed_filters: Dict[str, Any],
        aoi_bbox: Optional[List[float]] = None,
    ) -> Tuple[float, List[str]]:
        reasons: List[str] = []
        score = 0.0

        # 1. Semantic match
        target_class = parsed_filters.get("semantic_class")
        if target_class and target_class.upper() in event.semantic_class.upper():
            score += 0.35
            reasons.append(f"Semantic match: {event.semantic_class.replace('_', ' ').lower()}")
        elif not target_class:
            score += 0.20

        # 2. State match
        target_state = parsed_filters.get("state")
        if target_state and event.state.value == target_state:
            score += 0.25
            reasons.append(f"Event state: {event.state.value.lower()}")
        elif not target_state and event.state.value == "PERSISTENT":
            score += 0.15

        # 3. Spatial overlap
        if aoi_bbox and event.bounding_box and len(event.bounding_box) >= 4 and len(aoi_bbox) >= 4:
            iou = compute_bbox_iou(event.bounding_box, aoi_bbox)
            if iou > 0.0:
                spatial_pts = min(0.25, 0.10 + (0.15 * iou))
                score += spatial_pts
                reasons.append(f"Spatial overlap: {round(iou * 100)}% IoU with query AOI")
        else:
            score += 0.15

        # 4. Confidence
        conf_pts = min(0.15, 0.15 * event.confidence)
        score += conf_pts
        if event.confidence >= 0.75:
            reasons.append(f"High confidence ({round(event.confidence * 100)}%)")

        if not reasons:
            reasons.append("Historical Earth Observation match")

        return round(min(1.0, score), 3), reasons

    @classmethod
    def score_finding(
        cls,
        finding: PersistentFinding,
        parsed_filters: Dict[str, Any],
        aoi_bbox: Optional[List[float]] = None,
    ) -> Tuple[float, List[str]]:
        reasons: List[str] = []
        score = 0.0

        target_class = parsed_filters.get("semantic_class")
        if target_class and target_class.upper() in finding.semantic_class.upper():
            score += 0.40
            reasons.append(f"Semantic match: {finding.semantic_class.replace('_', ' ').lower()}")
        elif not target_class:
            score += 0.25

        if aoi_bbox and finding.bounding_box and len(finding.bounding_box) >= 4 and len(aoi_bbox) >= 4:
            iou = compute_bbox_iou(finding.bounding_box, aoi_bbox)
            if iou > 0.0:
                score += min(0.35, 0.15 + (0.20 * iou))
                reasons.append("Located within specified AOI bounds")
        else:
            score += 0.20

        conf_pts = min(0.25, 0.25 * finding.confidence)
        score += conf_pts
        if finding.confidence >= 0.80:
            reasons.append(f"High model confidence ({round(finding.confidence * 100)}%)")

        if not reasons:
            reasons.append("Empirical observation record")

        return round(min(1.0, score), 3), reasons
