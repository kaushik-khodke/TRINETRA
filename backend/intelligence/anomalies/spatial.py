"""
TRINETRA Phase 7 — Spatial Anomaly Detection
Detects isolated spatial outliers and unexpected new localized activity clusters.
"""

from typing import List, Optional, Tuple
from intelligence.events.matcher import haversine_distance_km


class SpatialAnomalyDetector:
    """
    Flags geographic change clusters that occur far outside expected regional footprints.
    """

    @classmethod
    def detect_spatial_outlier(
        cls,
        candidate_bbox: List[float],
        historical_centroids: List[Tuple[float, float]],
        max_normal_radius_km: float = 15.0,
    ) -> Tuple[bool, float, str]:
        if not candidate_bbox or len(candidate_bbox) < 4 or len(historical_centroids) < 3:
            return False, 0.0, "INSUFFICIENT_BASELINE"

        c_lat = (candidate_bbox[1] + candidate_bbox[3]) / 2.0
        c_lon = (candidate_bbox[0] + candidate_bbox[2]) / 2.0

        min_dist_km = min(haversine_distance_km(c_lat, c_lon, h_lat, h_lon) for h_lat, h_lon in historical_centroids)

        if min_dist_km > max_normal_radius_km:
            return (
                True,
                round(min_dist_km, 2),
                f"Spatial outlier: Detected change is {round(min_dist_km, 1)} km from established activity cluster (threshold: {max_normal_radius_km} km).",
            )

        return False, round(min_dist_km, 2), "Within established geographic envelope."
