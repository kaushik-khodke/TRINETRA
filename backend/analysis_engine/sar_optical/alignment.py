"""
TRINETRA Analysis Engine — SAR-Optical Coregistration & Overlap Verification
Validates spatial intersection and coregistration between multimodal observations.
"""

from typing import Dict, Any, List, Tuple
from analysis_engine.errors import PreprocessingFailureError


class CrossModalAlignmentChecker:
    @staticmethod
    def verify_alignment(
        opt_bounds: List[float],
        sar_bounds: List[float],
        opt_crs: str,
        sar_crs: str,
    ) -> Dict[str, Any]:
        """
        Validates spatial intersection and computes overlap percentage.
        """
        min_lon_o, min_lat_o, max_lon_o, max_lat_o = opt_bounds
        min_lon_s, min_lat_s, max_lon_s, max_lat_s = sar_bounds

        # Intersection bounds
        inter_min_lon = max(min_lon_o, min_lon_s)
        inter_min_lat = max(min_lat_o, min_lat_s)
        inter_max_lon = min(max_lon_o, max_lon_s)
        inter_max_lat = min(max_lat_o, max_lat_s)

        if inter_min_lon >= inter_max_lon or inter_min_lat >= inter_max_lat:
            raise PreprocessingFailureError(
                "Zero spatial overlap between Optical and SAR observations. Cross-modal analysis requires overlapping coverage."
            )

        inter_area = (inter_max_lon - inter_min_lon) * (inter_max_lat - inter_min_lat)
        opt_area = (max_lon_o - min_lon_o) * (max_lat_o - min_lat_o)
        overlap_pct = round(float(inter_area / opt_area) * 100.0, 2) if opt_area > 0 else 100.0

        return {
            "compatible": True,
            "spatial_overlap_pct": overlap_pct,
            "intersection_bounds": [inter_min_lon, inter_min_lat, inter_max_lon, inter_max_lat],
            "crs_match": opt_crs == sar_crs,
        }
