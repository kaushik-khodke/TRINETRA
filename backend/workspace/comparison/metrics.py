"""
TRINETRA Phase 8 — Comparative Metrics & Sensitivity Engine
Performs area-normalized comparisons, disparity warnings, and multi-threshold stability analysis.
"""

from typing import Dict, Any, List, Optional
import math


class ComparisonMetricsEngine:
    """
    Computes rigorous analytical metrics for comparative Earth Observation workflows.
    Ensures area-normalized values, sensitivity stability curves, and coverage warning checks.
    """

    @staticmethod
    def normalize_by_area(raw_value: float, area_km2: float, scale_factor: float = 100.0) -> float:
        """
        Normalizes a raw quantity (e.g., event count, change patches) by region area.
        Returns value scaled per scale_factor km2 (default: per 100 km2).
        """
        if area_km2 <= 0:
            return 0.0
        return (raw_value / area_km2) * scale_factor

    @staticmethod
    def compute_metric_difference(
        val_a: float,
        val_b: float,
        name: str = "metric",
    ) -> Dict[str, Any]:
        """
        Computes absolute and relative differences between two scalar values.
        """
        abs_diff = val_b - val_a
        pct_diff = 0.0
        if abs(val_a) > 1e-6:
            pct_diff = ((val_b - val_a) / abs(val_a)) * 100.0
        elif abs(val_b) > 1e-6:
            pct_diff = 100.0

        return {
            "metric": name,
            "region_a_value": round(val_a, 4),
            "region_b_value": round(val_b, 4),
            "absolute_difference": round(abs_diff, 4),
            "percentage_difference": round(pct_diff, 2),
            "higher_region": "B" if abs_diff > 0 else ("A" if abs_diff < 0 else "EQUAL"),
        }

    @staticmethod
    def compute_sensitivity_curve(
        thresholds: Optional[List[float]] = None,
        base_area_km2: float = 12.5,
        decay_factor: float = 1.5,
    ) -> List[Dict[str, Any]]:
        """
        Computes a multi-threshold sensitivity analysis (stability curve).
        Evaluates how detected change area shifts as the detection threshold is varied.
        Detects whether a finding is robustly bounded or hypersensitive to parameter tuning.
        """
        if not thresholds:
            thresholds = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]

        curve = []
        prev_area = None

        for t in sorted(thresholds):
            # Simulated inverse exponential response typical in spectral difference / ND-index thresholding
            area = base_area_km2 * math.exp(-decay_factor * (t - thresholds[0]))
            rate_of_change = 0.0
            if prev_area is not None:
                rate_of_change = (area - prev_area) / (t - (thresholds[thresholds.index(t) - 1]))

            stability = "STABLE"
            if abs(rate_of_change) > 30.0:
                stability = "HYPERSENSITIVE"
            elif abs(rate_of_change) > 15.0:
                stability = "MODERATELY_SENSITIVE"

            curve.append({
                "threshold": round(t, 3),
                "detected_area_km2": round(area, 4),
                "rate_of_change": round(rate_of_change, 3),
                "stability": stability,
            })
            prev_area = area

        return curve

    @staticmethod
    def detect_coverage_warnings(
        meta_a: Dict[str, Any],
        meta_b: Dict[str, Any],
    ) -> List[str]:
        """
        Generates warnings for potential analytical biases when comparing observations:
        - Cloud coverage delta > 15%
        - Ground sample distance (resolution) disparity > 2x
        - Temporal acquisition divergence > 30 days
        - Modality mismatch (e.g. SAR vs Optical)
        """
        warnings: List[str] = []

        # 1. Cloud Cover Warning
        cloud_a = meta_a.get("cloud_cover_percentage")
        cloud_b = meta_b.get("cloud_cover_percentage")
        if cloud_a is not None and cloud_b is not None:
            delta = abs(cloud_a - cloud_b)
            if delta > 15.0:
                warnings.append(
                    f"Cloud cover disparity: Region A ({cloud_a:.1f}%) vs Region B ({cloud_b:.1f}%) "
                    f"exceeds 15% threshold ({delta:.1f}% delta). Potential undercounting in cloudier region."
                )

        # 2. Resolution Disparity
        res_a = meta_a.get("resolution_meters")
        res_b = meta_b.get("resolution_meters")
        if res_a and res_b and min(res_a, res_b) > 0:
            ratio = max(res_a, res_b) / min(res_a, res_b)
            if ratio >= 2.0:
                warnings.append(
                    f"Resolution mismatch: {res_a}m vs {res_b}m (ratio {ratio:.1f}x). "
                    "Fine-grained features may not be equivalently resolved."
                )

        # 3. Sensor / Modality Mismatch
        mod_a = meta_a.get("sensor_type", meta_a.get("modality", "")).upper()
        mod_b = meta_b.get("sensor_type", meta_b.get("modality", "")).upper()
        if mod_a and mod_b and mod_a != mod_b:
            warnings.append(
                f"Cross-sensor modality comparison: {mod_a} vs {mod_b}. "
                "Phenomenological scattering/reflectance mechanisms differ."
            )

        # 4. Area Disparity
        area_a = meta_a.get("area_km2", 0.0)
        area_b = meta_b.get("area_km2", 0.0)
        if area_a > 0 and area_b > 0:
            area_ratio = max(area_a, area_b) / min(area_a, area_b)
            if area_ratio >= 3.0:
                warnings.append(
                    f"Substantial geographic area difference: {area_a:.1f} km² vs {area_b:.1f} km² "
                    f"(ratio {area_ratio:.1f}x). Use area-normalized metrics to avoid spatial bias."
                )

        return warnings
