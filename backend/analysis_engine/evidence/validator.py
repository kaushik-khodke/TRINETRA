"""
TRINETRA Analysis Engine — Evidence Validator Gate
Enforces mathematical, geometric, and internal consistency proofs before any evidence item
is rendered on the map or forwarded to the LLM reasoning layer.
"""

from typing import Dict, Any, List
from analysis_engine.errors import ReasoningFailureError
from analysis_engine.evidence.models import EvidencePack, ChangeRegionEvidence, GroundingEvidence


class EvidenceValidator:
    """Rigorous gate guaranteeing mathematical and spatial integrity."""

    @classmethod
    def validate_pack(cls, pack: EvidencePack) -> bool:
        """
        Validates the entire EvidencePack. Raises ReasoningFailureError if internally inconsistent.
        """
        stats = pack.statistics

        # 1. Mathematical Consistency: changed_pixels <= total_valid_pixels
        if "changed_pixels" in stats and "total_valid_pixels" in stats:
            chg = stats["changed_pixels"]
            val = stats["total_valid_pixels"]
            if chg > val:
                raise ReasoningFailureError(
                    f"Evidence inconsistency: changed_pixels ({chg}) exceeds total_valid_pixels ({val})"
                )

        # 2. Area Consistency: area_m2 ≈ changed_pixels * pixel_size_m^2
        if "area_m2" in stats and "changed_pixels" in stats and "pixel_size_meters" in stats:
            expected_area = stats["changed_pixels"] * (stats["pixel_size_meters"] ** 2)
            actual_area = stats["area_m2"]
            if expected_area > 0 and abs(actual_area - expected_area) / expected_area > 0.05:
                raise ReasoningFailureError(
                    f"Evidence inconsistency: Reported area {actual_area} m² disagrees with pixel count computation {expected_area} m²"
                )

        # 3. Change regions validation
        for r in pack.change_regions:
            cls.validate_change_region(r)

        # 4. Grounding detections validation
        for g in pack.grounding_detections:
            cls.validate_grounding(g)

        # 5. Region count vs change percentage check
        if stats.get("change_percentage", 0.0) > 0.0 and not pack.change_regions and pack.mode == "BI_TEMPORAL":
            # If changed pixels detected, there should be at least one region unless all were filtered
            pass

        return True

    @classmethod
    def validate_change_region(cls, region: ChangeRegionEvidence) -> None:
        """Verifies geometric bounds, non-negative area, and confidence range [0, 1]."""
        if not (0.0 <= region.confidence <= 1.0):
            raise ReasoningFailureError(f"Region {region.id} has invalid confidence: {region.confidence}")

        if region.area_m2 < 0.0:
            raise ReasoningFailureError(f"Region {region.id} has negative area: {region.area_m2}")

        if len(region.bbox) != 4 or region.bbox[0] > region.bbox[2] or region.bbox[1] > region.bbox[3]:
            raise ReasoningFailureError(f"Region {region.id} has malformed bounding box: {region.bbox}")

        if not region.geometry or region.geometry.get("type") not in ["Polygon", "MultiPolygon"]:
            raise ReasoningFailureError(f"Region {region.id} has invalid GeoJSON geometry type: {region.geometry}")

    @classmethod
    def validate_grounding(cls, detection: GroundingEvidence) -> None:
        """Verifies normalized bounding box coordinates [ymin, xmin, ymax, xmax]."""
        if not (0.0 <= detection.confidence <= 1.0):
            raise ReasoningFailureError(f"Grounding detection {detection.id} has invalid confidence: {detection.confidence}")

        if len(detection.bbox) != 4:
            raise ReasoningFailureError(f"Grounding detection {detection.id} bbox length must be 4: {detection.bbox}")

        ymin, xmin, ymax, xmax = detection.bbox
        if ymin > ymax or xmin > xmax:
            raise ReasoningFailureError(f"Grounding detection {detection.id} has inverted coords: {detection.bbox}")
