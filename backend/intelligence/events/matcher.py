"""
TRINETRA Phase 7 — Region and Event Matching
Computes multi-metric geospatial overlap, centroid haversine distance, and semantic compatibility.
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from intelligence.models import CanonicalRegion, EOEvent, PersistentFinding
from intelligence.events.models import EventMatchResult


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates true great-circle distance between two points in kilometers."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def compute_bbox_iou(box_a: List[float], box_b: List[float]) -> float:
    """Calculates Intersection-over-Union between two bounding boxes [min_lon, min_lat, max_lon, max_lat]."""
    if len(box_a) < 4 or len(box_b) < 4:
        return 0.0

    min_x = max(box_a[0], box_b[0])
    min_y = max(box_a[1], box_b[1])
    max_x = min(box_a[2], box_b[2])
    max_y = min(box_a[3], box_b[3])

    inter_w = max(0.0, max_x - min_x)
    inter_h = max(0.0, max_y - min_y)
    inter_area = inter_w * inter_h

    if inter_area <= 0.0:
        return 0.0

    area_a = max(0.0, box_a[2] - box_a[0]) * max(0.0, box_a[3] - box_a[1])
    area_b = max(0.0, box_b[2] - box_b[0]) * max(0.0, box_b[3] - box_b[1])
    union_area = area_a + area_b - inter_area

    if union_area <= 0.0:
        return 0.0

    return inter_area / union_area


def compute_bbox_centroid(bbox: List[float]) -> Tuple[float, float]:
    """Returns (lat, lon) centroid for bbox [min_lon, min_lat, max_lon, max_lat]."""
    if len(bbox) < 4:
        return (0.0, 0.0)
    lon = (bbox[0] + bbox[2]) / 2.0
    lat = (bbox[1] + bbox[3]) / 2.0
    return (lat, lon)


class RegionMatcher:
    """
    Identifies canonical spatial entities across multi-temporal acquisition epochs.
    """

    @classmethod
    def match_region(
        cls,
        candidate_bbox: List[float],
        existing_regions: List[CanonicalRegion],
        iou_threshold: float = 0.25,
        max_distance_km: float = 2.0,
    ) -> Optional[CanonicalRegion]:
        if not candidate_bbox or len(candidate_bbox) < 4 or not existing_regions:
            return None

        c_lat = (candidate_bbox[1] + candidate_bbox[3]) / 2.0
        c_lon = (candidate_bbox[0] + candidate_bbox[2]) / 2.0

        best_match: Optional[CanonicalRegion] = None
        best_score = 0.0

        for region in existing_regions:
            r_box = region.bounding_box
            if not r_box or len(r_box) < 4:
                continue

            iou = compute_bbox_iou(candidate_bbox, r_box)

            r_lat = (r_box[1] + r_box[3]) / 2.0
            r_lon = (r_box[0] + r_box[2]) / 2.0
            dist_km = haversine_distance_km(c_lat, c_lon, r_lat, r_lon)

            # Combined score: IoU weighting + distance decay
            if iou >= iou_threshold or dist_km <= max_distance_km:
                dist_score = max(0.0, 1.0 - (dist_km / max(1.0, max_distance_km)))
                score = (0.7 * iou) + (0.3 * dist_score)
                if score > best_score:
                    best_score = score
                    best_match = region

        return best_match


class EventMatcher:
    """
    Determines whether a new finding belongs to an existing ongoing EOEvent.
    """

    SEMANTIC_COMPATIBILITY = {
        "BUILT_UP_EXPANSION": {"BUILT_UP_EXPANSION", "CONSTRUCTION", "SURFACE_INFRASTRUCTURE", "URBAN_CHANGE"},
        "VEGETATION_LOSS": {"VEGETATION_LOSS", "DEFORESTATION", "AGRICULTURAL_DECLINE"},
        "WATER_BODY_DYNAMICS": {"WATER_BODY_DYNAMICS", "FLOOD_EXPANSION", "WATER_SURFACE_CHANGE"},
        "GENERAL_CHANGE": {"GENERAL_CHANGE", "BUILT_UP_EXPANSION", "VEGETATION_LOSS", "WATER_BODY_DYNAMICS"},
    }

    @classmethod
    def are_semantics_compatible(cls, class_a: str, class_b: str) -> bool:
        if class_a == class_b:
            return True
        allowed_a = cls.SEMANTIC_COMPATIBILITY.get(class_a, {class_a})
        allowed_b = cls.SEMANTIC_COMPATIBILITY.get(class_b, {class_b})
        return bool(allowed_a.intersection(allowed_b))

    @classmethod
    def match_finding_to_event(
        cls,
        finding: PersistentFinding,
        existing_events: List[EOEvent],
        iou_threshold: float = 0.15,
        max_distance_km: float = 3.0,
    ) -> EventMatchResult:
        if not existing_events or not finding.bounding_box or len(finding.bounding_box) < 4:
            return EventMatchResult(None, None, 0.0, 0.0, 999.0, False)

        f_lat = (finding.bounding_box[1] + finding.bounding_box[3]) / 2.0
        f_lon = (finding.bounding_box[0] + finding.bounding_box[2]) / 2.0

        best_event: Optional[EOEvent] = None
        best_score = 0.0
        best_iou = 0.0
        best_dist = 999.0

        for event in existing_events:
            # Check semantic compatibility
            if not cls.are_semantics_compatible(finding.semantic_class, event.semantic_class):
                continue

            e_box = event.bounding_box
            if not e_box or len(e_box) < 4:
                continue

            iou = compute_bbox_iou(finding.bounding_box, e_box)
            e_lat = (e_box[1] + e_box[3]) / 2.0
            e_lon = (e_box[0] + e_box[2]) / 2.0
            dist_km = haversine_distance_km(f_lat, f_lon, e_lat, e_lon)

            if iou >= iou_threshold or dist_km <= max_distance_km:
                dist_score = max(0.0, 1.0 - (dist_km / max(1.0, max_distance_km)))
                score = (0.65 * iou) + (0.35 * dist_score)
                if score > best_score:
                    best_score = score
                    best_event = event
                    best_iou = iou
                    best_dist = dist_km

        is_exact = best_iou >= 0.70 and best_score >= 0.75
        return EventMatchResult(
            matched_event=best_event,
            matched_region=None,
            score=best_score,
            spatial_iou=best_iou,
            centroid_distance_km=best_dist,
            is_exact_match=is_exact,
        )
