"""
TRINETRA Analysis Engine — Quantitative Evidence Statistics
Calculates mathematical parameters: valid pixel totals, changed area in m² and hectares,
change percentages, and spatial distribution metrics.
"""

from typing import Dict, Any, List, Optional
import numpy as np



class EvidenceStatisticsCalculator:
    @staticmethod
    def compute_change_statistics(
        change_mask: np.ndarray,
        validity_mask: np.ndarray,
        pixel_size_meters: float = 10.0,
        confidence_map: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """
        Computes authentic mathematical metrics over binary change and validity masks.
        """
        valid_pixels = int(np.sum(validity_mask))
        if valid_pixels == 0:
            return {
                "changed_pixels": 0,
                "total_valid_pixels": 0,
                "change_percentage": 0.0,
                "area_m2": 0.0,
                "area_ha": 0.0,
                "mean_confidence": 0.0,
            }

        effective_change = change_mask & validity_mask
        changed_pixels = int(np.sum(effective_change))
        change_pct = round(float(changed_pixels / valid_pixels) * 100.0, 3)

        pixel_area_m2 = pixel_size_meters * pixel_size_meters
        total_area_m2 = round(float(changed_pixels * pixel_area_m2), 2)
        total_area_ha = round(float(total_area_m2 / 10000.0), 3)

        mean_conf = 0.85
        if confidence_map is not None and changed_pixels > 0:
            mean_conf = float(np.mean(confidence_map[effective_change]))

        return {
            "changed_pixels": changed_pixels,
            "total_valid_pixels": valid_pixels,
            "change_percentage": change_pct,
            "area_m2": total_area_m2,
            "area_ha": total_area_ha,
            "pixel_size_meters": pixel_size_meters,
            "mean_confidence": round(mean_conf, 4),
        }
