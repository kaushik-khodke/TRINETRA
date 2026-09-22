"""
TRINETRA Phase 7 — Spatial Search Operations
Geodesic distance and bounding box intersection filters.
"""

from typing import List, Optional
from intelligence.events.matcher import haversine_distance_km, compute_bbox_iou


class SpatialSearchFilter:
    """
    Evaluates geospatial relationships using correct spherical geometry.
    """

    @classmethod
    def intersects_bbox(cls, box_a: Optional[List[float]], box_b: Optional[List[float]]) -> bool:
        if not box_a or not box_b or len(box_a) < 4 or len(box_b) < 4:
            return True  # If no filter specified, consider matching

        min_x1, min_y1, max_x1, max_y1 = box_a[:4]
        min_x2, min_y2, max_x2, max_y2 = box_b[:4]

        return not (max_x1 < min_x2 or max_x2 < min_x1 or max_y1 < min_y2 or max_y2 < min_y1)

    @classmethod
    def within_radius_km(
        cls,
        candidate_bbox: Optional[List[float]],
        center_lat: float,
        center_lon: float,
        radius_km: float,
    ) -> bool:
        if not candidate_bbox or len(candidate_bbox) < 4:
            return True

        c_lat = (candidate_bbox[1] + candidate_bbox[3]) / 2.0
        c_lon = (candidate_bbox[0] + candidate_bbox[2]) / 2.0
        dist = haversine_distance_km(center_lat, center_lon, c_lat, c_lon)
        return dist <= radius_km
