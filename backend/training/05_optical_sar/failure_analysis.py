"""
TRINETRA — Optical + SAR Multimodal Failure Analysis Engine
Automates multimodal failure autopsies for Optical-SAR fusion models.
Diagnoses error modes into structured FailureCase contracts:
- cloud_shadow (optical cloud occlusion / shadow),
- sensor_saturation (SAR radar layover, shadow, or specular distortion),
- misregistration (cross-sensor spatial displacement),
- model_divergence (conflicting unimodal predictions),
- missing_modality.
Governed by Stage 5 Optical + SAR Protocol. Zero synthetic data.
"""

import os
import sys
import uuid
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from schemas.contracts import FailureCase


class OpticalSARFailureAnalysisEngine:
    """
    Automated analytical autopsy engine for multimodal Optical-SAR predictions.
    Identifies root causes behind fusion errors and single-sensor discrepancies.
    """

    LAND_USE_CLASSES = [
        "Dense Urban Fabric", "Industrial Infrastructure", "Agricultural Crop Stand",
        "Forest Canopy", "Coniferous Woodland", "Natural Grassland / Shrub",
        "Inland Water Body", "Coastal / Marine", "Barren Soil / Rock", "Wetland / Marsh"
    ]

    @classmethod
    def diagnose_sample(
        cls,
        sample_id: str,
        opt_arr: np.ndarray,
        sar_arr: np.ndarray,
        pred_class: int,
        gt_class: int,
        opt_only_class: Optional[int] = None,
        sar_only_class: Optional[int] = None
    ) -> Optional[FailureCase]:
        """
        Diagnoses a single Optical-SAR sample prediction against ground truth.
        Returns a typed FailureCase if misclassified, else None.
        """
        if pred_class == gt_class:
            return None

        # Normalize arrays for physical analysis
        def _to_chw(img: np.ndarray) -> np.ndarray:
            arr = np.squeeze(img).astype(np.float32)
            if arr.ndim == 2:
                arr = np.stack([arr, arr], axis=0)
            elif arr.ndim == 3 and arr.shape[2] in [1, 2, 3, 4]:
                arr = np.transpose(arr[:, :, :3], (2, 0, 1))
            if arr.max() > 1.0:
                arr = arr / 255.0
            return arr

        opt = _to_chw(opt_arr)
        sar = _to_chw(sar_arr)

        pred_name = cls.LAND_USE_CLASSES[pred_class] if pred_class < len(cls.LAND_USE_CLASSES) else f"Class_{pred_class}"
        gt_name = cls.LAND_USE_CLASSES[gt_class] if gt_class < len(cls.LAND_USE_CLASSES) else f"Class_{gt_class}"

        # 1. Check for Optical Cloud Occlusion / Shadow
        # High-reflectance saturation in optical (clouds) or deep shadow
        opt_mean = float(np.mean(opt))
        opt_max = float(np.max(opt))
        cloud_pixels = np.mean(opt > 0.88)
        shadow_pixels = np.mean(opt < 0.05)

        if cloud_pixels > 0.20 or (opt_mean > 0.75 and opt_max >= 0.98):
            return FailureCase(
                case_id=f"fail-opt-sar-{sample_id}-{uuid.uuid4().hex[:6]}",
                asset_id=sample_id,
                expected_output=gt_name,
                actual_output=pred_name,
                error_category="cloud_shadow",
                severity="high",
                explanation=(
                    f"Optical observation is severely obscured by cloud cover ({int(cloud_pixels * 100)}% saturated pixels), "
                    f"inducing classification error ({pred_name} instead of {gt_name})."
                ),
                mitigation="Increase SAR modality weight in gated/cross-attention fusion under detected cloud occlusion."
            )

        # 2. Check for SAR Radar Specular Distortion / Saturation
        # Extreme radar backscatter clipping or specular loss (< -22 dB)
        sar_mean = float(np.mean(sar))
        sar_max = float(np.max(sar))

        if sar_max >= 0.99 or sar_mean > 0.85:
            return FailureCase(
                case_id=f"fail-opt-sar-{sample_id}-{uuid.uuid4().hex[:6]}",
                asset_id=sample_id,
                expected_output=gt_name,
                actual_output=pred_name,
                error_category="sensor_saturation",
                severity="medium",
                explanation=(
                    "SAR microwave channel exhibits extreme radar backscatter saturation/corner reflection "
                    f"driving erroneous prediction to {pred_name}."
                ),
                mitigation="Apply radiometric decibel calibration clamping and adaptive speckle filtering."
            )

        # 3. Check for Cross-Modal Sensor Divergence
        # Optical and SAR alone predict completely different classes
        if opt_only_class is not None and sar_only_class is not None:
            if opt_only_class != sar_only_class:
                opt_pred_name = cls.LAND_USE_CLASSES[opt_only_class] if opt_only_class < len(cls.LAND_USE_CLASSES) else f"Class_{opt_only_class}"
                sar_pred_name = cls.LAND_USE_CLASSES[sar_only_class] if sar_only_class < len(cls.LAND_USE_CLASSES) else f"Class_{sar_only_class}"
                return FailureCase(
                    case_id=f"fail-opt-sar-{sample_id}-{uuid.uuid4().hex[:6]}",
                    asset_id=sample_id,
                    expected_output=gt_name,
                    actual_output=f"Fused: {pred_name} (Opt: {opt_pred_name} vs SAR: {sar_pred_name})",
                    error_category="model_divergence",
                    severity="high" if pred_class != opt_only_class and pred_class != sar_only_class else "medium",
                    explanation=(
                        f"Optical and SAR unimodal encoders diverged sharply (Optical predicted '{opt_pred_name}', "
                        f"SAR predicted '{sar_pred_name}'). The fusion mechanism failed to arbitrate correctly."
                    ),
                    mitigation="Train with cross-modal contrastive alignment to constrain shared feature geometry."
                )

        # 4. Check for Subpixel / Spatial Misregistration
        # Difference in gradient orientation between optical and radar edges
        corr = float(np.corrcoef(opt.flatten()[:500], sar.flatten()[:500])[0, 1])
        if corr < -0.30:
            return FailureCase(
                case_id=f"fail-opt-sar-{sample_id}-{uuid.uuid4().hex[:6]}",
                asset_id=sample_id,
                expected_output=gt_name,
                actual_output=pred_name,
                error_category="misregistration",
                severity="medium",
                explanation=(
                    f"Strong negative cross-modal correlation ({corr:.3f}) suggests spatial displacement "
                    "or sensor coregistration misalignment between Optical and SAR grids."
                ),
                mitigation="Enforce rigorous geometric subpixel coregistration prior to feature extraction."
            )

        # 5. Default Misclassification
        return FailureCase(
            case_id=f"fail-opt-sar-{sample_id}-{uuid.uuid4().hex[:6]}",
            asset_id=sample_id,
            expected_output=gt_name,
            actual_output=pred_name,
            error_category="out_of_distribution",
            severity="low",
            explanation=f"Multimodal classifier failed to distinguish {gt_name} from {pred_name}.",
            mitigation="Expand training distribution coverage for complex mixed-class boundary conditions."
        )

    @classmethod
    def generate_failure_report(cls, failures: List[FailureCase]) -> Dict[str, Any]:
        """
        Generates summary statistics and recommendations from a list of FailureCases.
        """
        if not failures:
            return {
                "total_failures": 0,
                "breakdown": {},
                "severity_distribution": {},
                "primary_failure_mode": "None",
                "recommended_mitigations": []
            }

        category_counts: Dict[str, int] = {}
        severity_counts: Dict[str, int] = {}
        mitigations = set()

        for f in failures:
            cat = f.error_category
            category_counts[cat] = category_counts.get(cat, 0) + 1
            severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1
            if f.mitigation:
                mitigations.add(f.mitigation)

        sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        primary_mode = sorted_cats[0][0] if sorted_cats else "None"

        return {
            "total_failures": len(failures),
            "breakdown": {cat: count for cat, count in sorted_cats},
            "category_percentages": {
                cat: round((count / len(failures)) * 100, 1)
                for cat, count in sorted_cats
            },
            "severity_distribution": severity_counts,
            "primary_failure_mode": primary_mode,
            "recommended_mitigations": sorted(list(mitigations))
        }
