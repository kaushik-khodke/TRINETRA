"""
TRINETRA Failure Mining & High-Confidence Error Analysis Engine (Stage 9)
Governed by 09_STAGE_9_CALIBRATION.md and NON_NEGOTIABLE_PRINCIPLES.md.

Mines critical failure modes:
1. High-Confidence Wrong Cases (The most dangerous failure mode in defense/EO)
2. Low-Confidence Correct Cases (Underconfident successes)
3. Worst Cases (Largest probability error margin)
4. Common Failure Categories (Distribution by root cause)

Generates typed CalibrationAuditReport and FailureCase records.
"""

from typing import Dict, List, Optional, Any, Union, Tuple
import uuid
import numpy as np

try:
    from backend.schemas.contracts import CalibrationAuditReport, FailureCase
    from backend.calibration.calibrator import ReliabilityDiagram, compute_brier_score, compute_classwise_ece
except ImportError:
    from schemas.contracts import CalibrationAuditReport, FailureCase
    from calibration.calibrator import ReliabilityDiagram, compute_brier_score, compute_classwise_ece


class FailureMiner:
    """
    Analyzes model predictions to diagnose high-confidence errors,
    hesitant successes, and aggregate common failure categories.
    """

    @classmethod
    def diagnose_failure_category(
        cls,
        pred: Any,
        target: Any,
        confidence: float,
        task: str = "general",
        meta: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str]:
        """
        Diagnoses the specific root cause and technical explanation for an error.
        Returns: (error_category, explanation).
        """
        meta = meta or {}
        quality_flags = meta.get("quality_flags", [])

        # Priority 1: Data quality issues (clouds, saturation, shadows)
        if any("CLOUD" in f for f in quality_flags):
            return "cloud_shadow", "Predicted under severe cloud or haze occlusion"
        if any("SHADOW" in f for f in quality_flags):
            return "cloud_shadow", "Predicted in deep topographic or cloud shadow"
        if any("SATURATION" in f for f in quality_flags):
            return "sensor_saturation", "Sensor dynamic range clipping / detector saturation"

        # Priority 2: Spatial registration issues
        if any("OFFSET" in f or "UNALIGNED" in f for f in quality_flags):
            return "misregistration", "Subpixel spatial registration drift between rasters"

        # Priority 3: Domain-specific root causes
        if task == "change_detection":
            return "boundary_error", "Subtle building footprint boundary misclassification"
        elif task == "hyperspectral_classification":
            return "spectral_metamerism", "Metamerism between spectrally adjacent vegetation species"
        elif task == "multimodal_fusion":
            return "out_of_distribution", "Optical-SAR cross-modal feature disagreement"
        elif task == "vqa":
            return "other", "Visual referring expression grounding failure"

        # Default fallback
        if confidence >= 0.85:
            return "out_of_distribution", "High-confidence out-of-distribution feature misclassification"
        return "other", f"Prediction {pred} deviated from ground truth {target}"

    @classmethod
    def mine(
        cls,
        y_pred: np.ndarray,
        y_true: np.ndarray,
        confidences: np.ndarray,
        sample_ids: Optional[List[str]] = None,
        task: str = "general",
        dataset_name: str = "Benchmark Dataset",
        split: str = "test",
        high_conf_threshold: float = 0.75,
        low_conf_threshold: float = 0.50,
        uncalibrated_confidences: Optional[np.ndarray] = None,
        temperature: Optional[float] = None,
        class_probs: Optional[np.ndarray] = None,
        num_classes: Optional[int] = None,
        samples_meta: Optional[List[Dict[str, Any]]] = None
    ) -> CalibrationAuditReport:
        """
        Identifies high-confidence wrong, low-confidence correct, and worst cases,
        aggregating them into a comprehensive CalibrationAuditReport.
        """
        y_pred = np.asarray(y_pred).ravel()
        y_true = np.asarray(y_true).ravel()
        confidences = np.asarray(confidences, dtype=np.float64).ravel()
        n_samples = len(y_true)

        if sample_ids is None or len(sample_ids) != n_samples:
            sample_ids = [f"sample_{i:04d}" for i in range(n_samples)]

        if samples_meta is None or len(samples_meta) != n_samples:
            samples_meta = [{} for _ in range(n_samples)]

        uncal_conf = (
            np.asarray(uncalibrated_confidences, dtype=np.float64).ravel()
            if uncalibrated_confidences is not None
            else confidences
        )

        correctness = (y_pred == y_true).astype(float)

        # 1. Calibration Metrics
        rel_cal = ReliabilityDiagram.compute(confidences, correctness)
        rel_uncal = ReliabilityDiagram.compute(uncal_conf, correctness)

        cal_brier = rel_cal.brier_score
        uncal_brier = rel_uncal.brier_score

        # 2. Mine High-Confidence Wrong Cases (Critical!)
        high_conf_wrong: List[Dict[str, Any]] = []
        low_conf_correct: List[Dict[str, Any]] = []
        failure_category_counts: Dict[str, int] = {}

        for i in range(n_samples):
            pred_i = y_pred[i]
            true_i = y_true[i]
            conf_i = float(confidences[i])
            sid = sample_ids[i]
            meta_i = samples_meta[i]

            if pred_i != true_i:
                # Failure Case
                cat, expl = cls.diagnose_failure_category(pred_i, true_i, conf_i, task, meta_i)
                failure_category_counts[cat] = failure_category_counts.get(cat, 0) + 1

                if conf_i >= high_conf_threshold:
                    sev = "critical" if conf_i >= 0.85 else "high"
                    fc = FailureCase(
                        case_id=str(uuid.uuid4())[:8],
                        asset_id=sid,
                        actual_output=f"Predicted Class {pred_i} (conf={conf_i:.3f})",
                        expected_output=f"Ground Truth Class {true_i}",
                        error_category=cat,
                        severity=sev,
                        explanation=expl,
                        confidence_score=conf_i,
                        mitigation="Apply temperature calibration and verify spatial coregistration"
                    )
                    high_conf_wrong.append(fc.model_dump())
            else:
                # Correct Prediction
                if conf_i < low_conf_threshold:
                    low_conf_correct.append({
                        "case_id": str(uuid.uuid4())[:8],
                        "asset_id": sid,
                        "class": int(pred_i),
                        "confidence": round(conf_i, 3),
                        "status": "hesitant_correct",
                        "note": "Prediction correct but confidence under threshold"
                    })

        # 3. Mine Worst Cases (Sorted by error gap / loss)
        error_gaps = []
        for i in range(n_samples):
            if y_pred[i] != y_true[i]:
                gap = float(confidences[i])  # higher confidence on error = worse
                error_gaps.append((gap, i))
        error_gaps.sort(key=lambda x: x[0], reverse=True)

        worst_cases: List[Dict[str, Any]] = []
        for gap, idx in error_gaps[:10]:
            worst_cases.append({
                "asset_id": sample_ids[idx],
                "predicted": int(y_pred[idx]),
                "ground_truth": int(y_true[idx]),
                "confidence": round(float(confidences[idx]), 3),
                "error_gap": round(gap, 3)
            })

        # 4. Class-wise ECE if multi-class probabilities provided
        classwise = None
        if class_probs is not None and num_classes is not None and num_classes > 1:
            classwise = compute_classwise_ece(class_probs, y_true, num_classes)

        return CalibrationAuditReport(
            dataset_name=dataset_name,
            split=split,
            sample_count=n_samples,
            uncalibrated_ece=rel_uncal.ece,
            calibrated_ece=rel_cal.ece,
            uncalibrated_brier=uncal_brier,
            calibrated_brier=cal_brier,
            temperature=round(temperature, 3) if temperature is not None else None,
            worst_cases=worst_cases,
            high_confidence_wrong_cases=high_conf_wrong,
            low_confidence_correct_cases=low_conf_correct[:10],
            common_failure_categories=failure_category_counts,
            classwise_ece=classwise
        )
