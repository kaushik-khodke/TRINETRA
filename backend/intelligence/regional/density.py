"""
TRINETRA Phase 7 — Regional Change Density
Calculates spatial event density, changed-area concentration, and semantic diversity.
"""

from typing import List, Dict, Any


class RegionalDensityCalculator:
    """
    Computes spatial concentration metrics for Earth Observation events.
    """

    @classmethod
    def calculate_density(
        cls,
        event_count: int,
        total_area_ha: float,
        region_area_km2: float = 25.0,
    ) -> Dict[str, float]:
        reg_area = max(0.1, region_area_km2)
        event_density = event_count / reg_area
        area_density_pct = (total_area_ha / (reg_area * 100.0)) * 100.0  # 1 km2 = 100 ha

        return {
            "event_density_per_km2": round(event_density, 3),
            "area_density_pct": round(area_density_pct, 2),
            "total_area_ha": round(total_area_ha, 2),
            "region_area_km2": round(reg_area, 2),
        }
