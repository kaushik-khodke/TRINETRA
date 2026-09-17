"""
TRINETRA — Bi-Temporal Change Detection Failure Analysis Engine
Automates failure autopsies for change detection predictions.
Diagnoses error modes into structured FailureCase contracts:
- false_positive, false_negative, seasonal_change, misregistration,
  cloud_shadow, small_object_miss, boundary_error.
Governed by Stage 4 Change Detection Protocol. Zero synthetic data.
"""

import os
import sys
import uuid
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
from PIL import Image

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from schemas.contracts import FailureCase


class ChangeFailureAnalysisEngine:
    """
    Automated analytical diagnosis engine for bi-temporal change predictions.
    Identifies root causes behind false alarms and missed changes using physical
    and spatial morphological indicators.
    """

    @classmethod
    def diagnose_sample(
        cls,
        sample_id: str,
        t1_arr: np.ndarray,
        t2_arr: np.ndarray,
        pred_mask: np.ndarray,
        true_mask: np.ndarray,
        iou_threshold: float = 0.5
    ) -> Optional[FailureCase]:
        """
        Diagnoses a single sample prediction against ground truth.
        Returns a typed FailureCase if significant error exists, else None.
        """
        import scipy.ndimage as ndi

        # Normalize arrays to 2D (H, W)
        p_mask = np.squeeze(np.asarray(pred_mask)) >= 0.5
        t_mask = np.squeeze(np.asarray(true_mask)) >= 0.5

        if p_mask.shape != t_mask.shape:
            raise ValueError(f"Shape mismatch: pred {p_mask.shape} vs true {t_mask.shape}")

        h, w = p_mask.shape
        total_pixels = h * w

        tp = np.sum(p_mask & t_mask)
        fp = np.sum(p_mask & (~t_mask))
        fn = np.sum((~p_mask) & t_mask)

        union = tp + fp + fn
        iou = float(tp / (union + 1e-8)) if union > 0 else 1.0

        # If IoU meets threshold and no large false alarms, no failure case
        if iou >= iou_threshold and fp < (0.01 * total_pixels):
            return None

        # Determine severity
        error_ratio = (fp + fn) / total_pixels
        if error_ratio > 0.20 or iou < 0.10:
            severity = "high"
        elif error_ratio > 0.05 or iou < 0.35:
            severity = "medium"
        else:
            severity = "low"

        # Prepare normalized RGB images for visual checks
        def _to_chw(img: np.ndarray) -> np.ndarray:
            arr = np.squeeze(img).astype(np.float32)
            if arr.ndim == 2:
                arr = np.stack([arr, arr, arr], axis=0)
            elif arr.ndim == 3 and arr.shape[2] in [1, 3, 4]:
                arr = np.transpose(arr[:, :, :3], (2, 0, 1))
            if arr.max() > 1.0:
                arr = arr / 255.0
            return arr

        t1 = _to_chw(t1_arr)
        t2 = _to_chw(t2_arr)

        # 1. Check for Small Object Miss
        # If GT has small isolated objects (< 40 pixels) missed by prediction
        labeled_gt, num_gt = ndi.label(t_mask)
        small_miss_count = 0
        for obj_idx in range(1, num_gt + 1):
            obj_area = np.sum(labeled_gt == obj_idx)
            if obj_area < 40 and not np.any(p_mask[labeled_gt == obj_idx]):
                small_miss_count += 1

        if small_miss_count > 0 and (small_miss_count == num_gt or fn > fp * 2):
            return FailureCase(
                case_id=f"fail-{sample_id}-{uuid.uuid4().hex[:6]}",
                asset_id=sample_id,
                expected_output=f"{num_gt} changed objects (GT area: {int(np.sum(t_mask))} px)",
                actual_output=f"Missed {small_miss_count} small targets (IoU: {iou:.3f})",
                error_category="small_object_miss",
                severity=severity,
                explanation=(
                    f"Sample contains {small_miss_count} small changed objects (< 40 px) "
                    "that were lost during downsampling or spatial pooling in the encoder."
                ),
                mitigation="Incorporate multi-scale high-resolution feature pyramids or adjust Dice loss weighting."
            )

        # 2. Check for Boundary Error
        # If the majority of errors are adjacent to the ground truth boundary
        dilated_gt = ndi.binary_dilation(t_mask, iterations=2)
        eroded_gt = ndi.binary_erosion(t_mask, iterations=2)
        gt_boundary_band = dilated_gt & (~eroded_gt)

        boundary_errors = np.sum((p_mask != t_mask) & gt_boundary_band)
        total_errors = fp + fn
        if total_errors > 0 and (boundary_errors / total_errors) > 0.65:
            return FailureCase(
                case_id=f"fail-{sample_id}-{uuid.uuid4().hex[:6]}",
                asset_id=sample_id,
                expected_output="Crisp object contours matching ground truth",
                actual_output=f"Perimeter dilation/erosion discrepancy (IoU: {iou:.3f})",
                error_category="boundary_error",
                severity="low" if severity == "medium" else severity,
                explanation=(
                    f"{int((boundary_errors / total_errors) * 100)}% of error pixels reside "
                    "strictly along the perimeter boundary of genuine changes."
                ),
                mitigation="Add morphological contour loss or edge-aware boundary regularization."
            )

        # 3. Check for Cloud / Shadow False Alarm
        # Detect sharp drop in luminance or deep shadow regions in T2 not present in T1
        fp_mask = p_mask & (~t_mask)
        if np.sum(fp_mask) > 50:
            lum1 = 0.299 * t1[0] + 0.587 * t1[1] + 0.114 * t1[2]
            lum2 = 0.299 * t2[0] + 0.587 * t2[1] + 0.114 * t2[2]
            fp_lum1 = float(np.mean(lum1[fp_mask]))
            fp_lum2 = float(np.mean(lum2[fp_mask]))

            if fp_lum2 < 0.18 and (fp_lum1 - fp_lum2) > 0.25:
                return FailureCase(
                    case_id=f"fail-{sample_id}-{uuid.uuid4().hex[:6]}",
                    asset_id=sample_id,
                    expected_output="No structural change in shadow region",
                    actual_output=f"False alarm triggered by cast shadow (Mean Lum T1={fp_lum1:.2f}, T2={fp_lum2:.2f})",
                    error_category="cloud_shadow",
                    severity=severity,
                    explanation=(
                        "Sudden local illumination drop in post-change observation mistaken for "
                        "structural modification."
                    ),
                    mitigation="Apply photometric shadow augmentation or HSV saturation/value invariant normalization."
                )

        # 4. Check for Misregistration Artifact
        # If false alarms are narrow linear fringes along high-contrast edges
        if np.sum(fp_mask) > 20:
            sobel_t1 = ndi.sobel(lum1 if 'lum1' in locals() else t1[0])
            sobel_t2 = ndi.sobel(lum2 if 'lum2' in locals() else t2[0])
            edge_energy = np.hypot(sobel_t1, sobel_t2)
            if np.mean(edge_energy[fp_mask]) > 1.5 * np.mean(edge_energy):
                return FailureCase(
                    case_id=f"fail-{sample_id}-{uuid.uuid4().hex[:6]}",
                    asset_id=sample_id,
                    expected_output="Stable edge registration",
                    actual_output="Linear fringe false alarm along structural edge",
                    error_category="misregistration",
                    severity=severity,
                    explanation=(
                        "Subpixel misregistration between T1 and T2 creates high-frequency edge difference "
                        "erroneously classified as change."
                    ),
                    mitigation="Utilize phase-correlation subpixel coregistration prior to change inference."
                )

        # 5. Check for Seasonal / Phenological Vegetative Shift
        if np.sum(fp_mask) > 100:
            # Green band dominance differential
            green_diff = np.abs(t2[1] - t1[1])
            if float(np.mean(green_diff[fp_mask])) > 0.15:
                return FailureCase(
                    case_id=f"fail-{sample_id}-{uuid.uuid4().hex[:6]}",
                    asset_id=sample_id,
                    expected_output="Unchanged built-up structure",
                    actual_output="Vegetation greening/browning falsely flagged as change",
                    error_category="seasonal_change",
                    severity=severity,
                    explanation="Phenological or seasonal vegetation variation confused with genuine land transformation.",
                    mitigation="Train with cross-season pair augmentations and NDRE/NDVI differential suppression."
                )

        # 6. Default Categorization: False Positive vs False Negative
        if fp > fn:
            return FailureCase(
                case_id=f"fail-{sample_id}-{uuid.uuid4().hex[:6]}",
                asset_id=sample_id,
                expected_output=f"Change area: {int(np.sum(t_mask))} px",
                actual_output=f"Over-predicted change area: {int(np.sum(p_mask))} px (FP: {fp})",
                error_category="false_positive",
                severity=severity,
                explanation="Model produced excess false positive change detections across unchanged surface.",
                mitigation="Increase threshold or incorporate hard negative mining during training."
            )
        else:
            return FailureCase(
                case_id=f"fail-{sample_id}-{uuid.uuid4().hex[:6]}",
                asset_id=sample_id,
                expected_output=f"Change area: {int(np.sum(t_mask))} px",
                actual_output=f"Under-predicted change area: {int(np.sum(p_mask))} px (FN: {fn})",
                error_category="false_negative",
                severity=severity,
                explanation="Model missed genuine ground-truth structural transformation.",
                mitigation="Increase weight of change class or increase Dice loss penalty."
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
