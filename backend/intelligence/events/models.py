"""
TRINETRA Phase 7 — Event Subsystem Helper Models
"""

from typing import Dict, Any, List, Optional
from intelligence.models import EOEvent, CanonicalRegion, EventState


class EventMatchResult:
    def __init__(
        self,
        matched_event: Optional[EOEvent],
        matched_region: Optional[CanonicalRegion],
        score: float,
        spatial_iou: float,
        centroid_distance_km: float,
        is_exact_match: bool,
    ):
        self.matched_event = matched_event
        self.matched_region = matched_region
        self.score = round(score, 3)
        self.spatial_iou = round(spatial_iou, 3)
        self.centroid_distance_km = round(centroid_distance_km, 3)
        self.is_exact_match = is_exact_match

    def to_dict(self) -> Dict[str, Any]:
        return {
            "matched_event_id": self.matched_event.event_id if self.matched_event else None,
            "matched_region_id": self.matched_region.canonical_region_id if self.matched_region else None,
            "score": self.score,
            "spatial_iou": self.spatial_iou,
            "centroid_distance_km": self.centroid_distance_km,
            "is_exact_match": self.is_exact_match,
        }
