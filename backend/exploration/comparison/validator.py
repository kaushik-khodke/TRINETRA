"""
TRINETRA / Shanetra Geospatial Exploration Engine
Observation Comparison Validator
Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
Validates pairing compatibility, self-comparison prevention, temporal delta, and spatial overlap.
"""

from datetime import datetime
from typing import List, Optional, Tuple
from shapely.geometry import box
from exploration.comparison.models import (
    ComparisonMode,
    ComparisonValidationRequest,
    ComparisonValidationResponse,
)
from exploration.temporal.normalizer import ObservationSummary
from exploration.service import explore_service


class ComparisonValidator:
    """Validates compatibility between two observations for side-by-side or split viewing."""

    @classmethod
    def validate(
        cls,
        obs_a: Optional[ObservationSummary],
        obs_b: Optional[ObservationSummary],
        mode: ComparisonMode = ComparisonMode.SPLIT,
    ) -> ComparisonValidationResponse:
        warnings: List[str] = []
        errors: List[str] = []

        # 1. Existence check
        if not obs_a:
            return ComparisonValidationResponse(
                compatible=False,
                errors=["Observation A not found."],
            )
        if not obs_b:
            return ComparisonValidationResponse(
                compatible=False,
                errors=["Observation B not found."],
            )

        # 2. Self-comparison prevention
        if obs_a.id == obs_b.id:
            return ComparisonValidationResponse(
                compatible=False,
                errors=["Cannot compare an observation with itself."],
                observation_a=obs_a,
                observation_b=obs_b,
            )

        # 3. Temporal delta calculation
        delta_days: Optional[float] = None
        try:
            dt_a = datetime.fromisoformat(obs_a.datetime.replace("Z", "+00:00"))
            dt_b = datetime.fromisoformat(obs_b.datetime.replace("Z", "+00:00"))
            delta_days = round(abs((dt_b - dt_a).total_seconds()) / 86400.0, 1)
        except Exception:
            warnings.append("Could not compute temporal delta due to date format variance.")

        # 4. Spatial overlap calculation
        overlap_pct: Optional[float] = None
        if obs_a.bbox and obs_b.bbox and len(obs_a.bbox) == 4 and len(obs_b.bbox) == 4:
            try:
                geom_a = box(*obs_a.bbox)
                geom_b = box(*obs_b.bbox)
                inter = geom_a.intersection(geom_b)
                if inter.is_empty:
                    errors.append("Observations have no spatial overlap (disjoint footprints).")
                    return ComparisonValidationResponse(
                        compatible=False,
                        errors=errors,
                        observation_a=obs_a,
                        observation_b=obs_b,
                        temporal_delta_days=delta_days,
                        spatial_overlap_pct=0.0,
                    )
                min_area = min(geom_a.area, geom_b.area)
                if min_area > 0:
                    overlap_pct = round((inter.area / min_area) * 100.0, 1)
                    if overlap_pct < 10.0:
                        errors.append(f"Spatial overlap ({overlap_pct}%) is insufficient for comparison (< 10%).")
                        return ComparisonValidationResponse(
                            compatible=False,
                            errors=errors,
                            observation_a=obs_a,
                            observation_b=obs_b,
                            temporal_delta_days=delta_days,
                            spatial_overlap_pct=overlap_pct,
                        )
                    elif overlap_pct < 50.0:
                        warnings.append(f"Partial spatial overlap ({overlap_pct}%). Footprints do not completely align.")
            except Exception as e:
                warnings.append(f"Could not calculate exact spatial overlap: {e}")

        # 5. Metadata difference warnings
        if obs_a.collection != obs_b.collection:
            warnings.append(f"Comparing different collections: '{obs_a.collection}' vs '{obs_b.collection}'.")

        if obs_a.platform and obs_b.platform and obs_a.platform != obs_b.platform:
            warnings.append(f"Different satellite platforms: '{obs_a.platform}' vs '{obs_b.platform}'.")

        return ComparisonValidationResponse(
            compatible=len(errors) == 0,
            warnings=warnings,
            errors=errors,
            observation_a=obs_a,
            observation_b=obs_b,
            temporal_delta_days=delta_days,
            spatial_overlap_pct=overlap_pct,
        )
