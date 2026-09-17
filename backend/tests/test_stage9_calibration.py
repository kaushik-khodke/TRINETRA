"""
TRINETRA Stage 9 Test Suite: Confidence, Uncertainty and Failure Analysis
Governed by 09_STAGE_9_CALIBRATION.md and NON_NEGOTIABLE_PRINCIPLES.md.

Validates:
1. Temperature Scaling optimization on validation logits reduces ECE while preserving accuracy.
2. Anti-leakage policy: fitting calibration parameters on test data raises DataLeakageError.
3. Reliability Diagram computation: accurate binning, ECE, and MCE calculation.
4. Multi-class and binary Brier score calculation against ground truth.
5. Class-wise calibration error computation surfacing class-imbalanced overconfidence.
6. Isotonic regression and Platt logistic scaling.
7. Explicit confidence semantics disambiguation (probability_class_correctness vs pixel vs region).
8. Orthogonal uncertainty decomposition (aleatoric, epistemic, data-quality, registration).
9. Failure miner: mining safety-critical high-confidence wrong cases and hesitant correct cases.
10. End-to-end integration into EvidencePackage and ConfidenceCalibrationTraceability.
"""

import os
import sys
import pytest
import numpy as np
import torch
import torch.nn as nn

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
project_root = os.path.abspath(os.path.join(backend_root, ".."))
for p in [backend_root, project_root]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from schemas.contracts import (
        ConfidenceCalibrationTraceability,
        ReliabilityDiagramData,
        UncertaintyReport,
        CalibrationAuditReport,
        FailureCase,
        CandidateAnswer
    )
    from core.exceptions import DataLeakageError
    from calibration.calibrator import (
        TemperatureScaler,
        IsotonicCalibrator,
        PlattScaler,
        ReliabilityDiagram,
        compute_brier_score,
        compute_classwise_ece
    )
    from calibration.uncertainty import (
        ConfidenceSemantics,
        UncertaintyDecompositionEngine
    )
    from calibration.failure_miner import FailureMiner
    from services.vqa.evidence_engine import VQAEvidenceEngine
except ImportError:
    from backend.schemas.contracts import (
        ConfidenceCalibrationTraceability,
        ReliabilityDiagramData,
        UncertaintyReport,
        CalibrationAuditReport,
        FailureCase,
        CandidateAnswer
    )
    from backend.core.exceptions import DataLeakageError
    from backend.calibration.calibrator import (
        TemperatureScaler,
        IsotonicCalibrator,
        PlattScaler,
        ReliabilityDiagram,
        compute_brier_score,
        compute_classwise_ece
    )
    from backend.calibration.uncertainty import (
        ConfidenceSemantics,
        UncertaintyDecompositionEngine
    )
    from backend.calibration.failure_miner import FailureMiner
    from backend.services.vqa.evidence_engine import VQAEvidenceEngine



# ==============================================================================
# 1. Temperature Scaling Optimization & ECE Reduction
# ==============================================================================
def test_temperature_scaling_optimization_and_ece_reduction():
    """Verify temperature scaling optimizes T on validation set and reduces ECE."""
    # Synthetic overconfident validation set
    np.random.seed(42)
    torch.manual_seed(42)
    n_val = 500
    num_classes = 5

    # Generate uncalibrated overconfident logits (large magnitude logits)
    val_targets = np.random.randint(0, num_classes, size=n_val)
    val_logits = np.random.normal(loc=0.0, scale=1.0, size=(n_val, num_classes))
    # Make correct class have highest logit with overconfidence
    for i in range(n_val):
        if np.random.rand() < 0.70:  # 70% accuracy
            val_logits[i, val_targets[i]] += 4.5  # high confidence ~95%
        else:
            wrong_cls = (val_targets[i] + 1) % num_classes
            val_logits[i, wrong_cls] += 3.5

    uncal_probs = torch.softmax(torch.from_numpy(val_logits), dim=-1).numpy()
    uncal_preds = np.argmax(uncal_probs, axis=1)
    uncal_confs = np.max(uncal_probs, axis=1)
    uncal_correctness = (uncal_preds == val_targets).astype(float)

    uncal_diag = ReliabilityDiagram.compute(uncal_confs, uncal_correctness)

    scaler = TemperatureScaler(init_temp=1.0)
    opt_temp = scaler.fit(val_logits, val_targets, is_val_split=True)

    assert scaler.is_fitted is True
    assert opt_temp > 1.0  # Overconfident model requires T > 1 to soften probabilities

    cal_probs = scaler.calibrate(val_logits)
    cal_preds = np.argmax(cal_probs, axis=1)
    cal_confs = np.max(cal_probs, axis=1)
    cal_correctness = (cal_preds == val_targets).astype(float)

    # Rank preservation: accuracy must remain EXACTLY identical
    assert np.array_equal(uncal_preds, cal_preds)
    assert np.mean(uncal_correctness) == np.mean(cal_correctness)

    cal_diag = ReliabilityDiagram.compute(cal_confs, cal_correctness)

    # ECE must decrease significantly after temperature scaling
    assert cal_diag.ece < uncal_diag.ece


# ==============================================================================
# 2. Anti-Leakage Policy Enforcement
# ==============================================================================
def test_temperature_scaling_anti_leakage_guard():
    """Verify that fitting calibration parameters on test data raises DataLeakageError."""
    scaler = TemperatureScaler()
    dummy_logits = np.random.randn(10, 4)
    dummy_labels = np.random.randint(0, 4, size=10)

    # Calling fit with is_val_split=False must raise anti-leakage error
    with pytest.raises(Exception) as exc_info:
        scaler.fit(dummy_logits, dummy_labels, is_val_split=False)
    assert "anti-leakage" in str(exc_info.value).lower()


# ==============================================================================
# 3. Reliability Diagram & Bin Statistics
# ==============================================================================
def test_reliability_diagram_and_binning():
    """Verify ReliabilityDiagram correctly computes bin statistics, ECE, and MCE."""
    # Perfectly calibrated case: 10 bins, 100 samples per bin
    confidences = []
    correctness = []

    for b in range(10):
        bin_conf = (b + 0.5) / 10.0
        n_samples_bin = 100
        n_correct = int(bin_conf * n_samples_bin)
        confs = [bin_conf] * n_samples_bin
        corr = [1.0] * n_correct + [0.0] * (n_samples_bin - n_correct)
        confidences.extend(confs)
        correctness.extend(corr)

    diag = ReliabilityDiagram.compute(np.array(confidences), np.array(correctness), n_bins=10)

    assert isinstance(diag, ReliabilityDiagramData) or diag.__class__.__name__ == "ReliabilityDiagramData"
    assert len(diag.bin_accuracies) == 10
    assert len(diag.bin_confidences) == 10
    assert len(diag.bin_counts) == 10
    assert sum(diag.bin_counts) == 1000
    # In near-perfect calibration, ECE is very low (< 0.02)
    assert diag.ece < 0.02
    assert diag.mce < 0.05
    assert diag.brier_score >= 0.0


# ==============================================================================
# 4. Multi-class and Binary Brier Score
# ==============================================================================
def test_brier_score_computation():
    """Verify multi-class and binary Brier calibration score calculation."""
    # 1. Perfect predictions: Brier score = 0.0
    perfect_probs = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    perfect_targets = np.array([0, 1])
    assert compute_brier_score(perfect_probs, perfect_targets, num_classes=3) == 0.0

    # 2. Complete wrong predictions: Brier score = 2.0
    wrong_probs = np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 0.0]])
    assert compute_brier_score(wrong_probs, perfect_targets, num_classes=3) == 2.0

    # 3. Binary case
    binary_probs = np.array([0.9, 0.1, 0.8])
    binary_targets = np.array([1, 0, 1])
    brier_bin = compute_brier_score(binary_probs, binary_targets)
    assert 0.0 <= brier_bin <= 0.05


# ==============================================================================
# 5. Class-Wise Calibration Error
# ==============================================================================
def test_classwise_calibration_error():
    """Verify class-wise ECE computation to detect class-imbalanced overconfidence."""
    n = 100
    num_classes = 3
    probs = np.zeros((n, num_classes))
    # Class 0: overconfident wrong
    probs[:40, 0] = 0.95
    probs[:40, 1] = 0.05
    # Class 1: well calibrated
    probs[40:80, 1] = 0.70
    probs[40:80, 2] = 0.30
    # Class 2: uniform
    probs[80:, 2] = 0.50
    probs[80:, 0] = 0.50

    targets = np.array([1] * 40 + [1] * 30 + [2] * 10 + [2] * 20)

    class_ece = compute_classwise_ece(probs, targets, num_classes=num_classes)
    assert len(class_ece) == 3
    assert "class_0" in class_ece
    assert "class_1" in class_ece
    assert "class_2" in class_ece
    # Class 0 was predicted with 0.95 confidence but 0% accuracy -> high ECE
    assert class_ece["class_0"] > 0.40


# ==============================================================================
# 6. Isotonic & Platt Calibration
# ==============================================================================
def test_isotonic_and_platt_calibration():
    """Verify non-parametric Isotonic Regression and parametric Platt Scaling."""
    val_scores = np.array([-2.0, -1.0, 0.0, 1.0, 2.0, 3.0])
    val_labels = np.array([0, 0, 0, 1, 1, 1])

    # Platt Scaler
    platt = PlattScaler()
    platt.fit(val_scores, val_labels, is_val_split=True)
    assert platt.is_fitted is True

    test_scores = np.array([-1.5, 2.5])
    cal_p = platt.calibrate(test_scores)
    assert cal_p[0] < cal_p[1]
    assert 0.0 <= cal_p[0] <= 1.0

    # Isotonic Calibrator
    iso = IsotonicCalibrator()
    val_probs = np.array([0.1, 0.2, 0.4, 0.6, 0.8, 0.9])
    iso.fit(val_probs, val_labels, is_val_split=True)
    assert iso.is_fitted is True

    iso_cal = iso.calibrate(np.array([0.15, 0.85]))
    assert iso_cal[0] <= iso_cal[1]


# ==============================================================================
# 7. Confidence Semantics Disambiguation
# ==============================================================================
def test_confidence_semantics_and_disambiguation():
    """Verify typed confidence semantics distinguish class, pixel, and region confidence."""
    s1 = ConfidenceSemantics.PROBABILITY_CLASS_CORRECTNESS
    s2 = ConfidenceSemantics.PROBABILITY_PIXEL_CORRECTNESS
    s3 = ConfidenceSemantics.PROBABILITY_REGION_DETECTION

    assert s1.value == "probability_class_correctness"
    assert s2.value == "probability_pixel_correctness"
    assert s3.value == "probability_region_detection"
    assert s1 != s2


# ==============================================================================
# 8. Multi-Source Uncertainty Decomposition
# ==============================================================================
def test_uncertainty_decomposition():
    """Verify separate computation of aleatoric, epistemic, data-quality, and registration uncertainties."""
    # 1. High aleatoric ambiguity (uniform distribution)
    uniform_p = np.array([0.25, 0.25, 0.25, 0.25])
    aleatoric_high = UncertaintyDecompositionEngine.compute_aleatoric_uncertainty(uniform_p)
    assert aleatoric_high > 0.95

    # Low aleatoric ambiguity (confident distribution)
    confident_p = np.array([0.98, 0.01, 0.005, 0.005])
    aleatoric_low = UncertaintyDecompositionEngine.compute_aleatoric_uncertainty(confident_p)
    assert aleatoric_low < 0.15

    # 2. Epistemic uncertainty with MC Dropout passes
    mc_passes = np.array([
        [0.9, 0.1],
        [0.4, 0.6],
        [0.1, 0.9]
    ])
    epistemic = UncertaintyDecompositionEngine.compute_epistemic_uncertainty(mc_predictions=mc_passes)
    assert epistemic > 0.30

    # 3. Data-quality uncertainty: synthetic saturated / blank image
    sat_img = np.ones((64, 64, 3), dtype=np.float32) * 255.0
    qual_score, flags = UncertaintyDecompositionEngine.compute_data_quality_uncertainty(sat_img)
    assert qual_score > 0.50
    assert any("SATURATION" in f for f in flags)

    # 4. Registration uncertainty
    align_report = {"is_aligned": True, "pixel_offset_x": 2.5, "pixel_offset_y": 1.0}
    reg_score, reg_flags = UncertaintyDecompositionEngine.compute_registration_uncertainty(align_report)
    assert reg_score > 0.30
    assert any("REGISTRATION_DRIFT" in f for f in reg_flags)

    # Complete decomposed report
    report = UncertaintyDecompositionEngine.decompose(
        probs=confident_p,
        semantics=ConfidenceSemantics.PROBABILITY_CLASS_CORRECTNESS,
        raster_data=sat_img,
        alignment_report=align_report
    )
    assert isinstance(report, UncertaintyReport) or report.__class__.__name__ == "UncertaintyReport"
    assert report.overall_confidence == 0.98
    assert len(report.quality_flags) >= 2


# ==============================================================================
# 9. Failure Mining: High-Confidence Wrong Cases
# ==============================================================================
def test_failure_miner_high_confidence_wrong_detection():
    """Verify FailureMiner identifies high-confidence wrong cases, worst cases, and builds audit report."""
    y_pred = np.array([0, 1, 2, 0, 1, 2, 0, 1])
    y_true = np.array([0, 1, 0, 0, 2, 2, 0, 1])  # indices 2 and 4 are wrong
    # Index 2: Predicted 2, True 0, Conf 0.88 -> HIGH CONFIDENCE WRONG!
    # Index 4: Predicted 1, True 2, Conf 0.55 -> LOW CONFIDENCE WRONG
    # Index 7: Predicted 1, True 1, Conf 0.42 -> LOW CONFIDENCE CORRECT!
    confidences = np.array([0.90, 0.85, 0.88, 0.92, 0.55, 0.82, 0.78, 0.42])

    audit = FailureMiner.mine(
        y_pred=y_pred,
        y_true=y_true,
        confidences=confidences,
        task="hyperspectral_classification",
        dataset_name="Indian Pines Hyperspectral AVIRIS Scene",
        split="test",
        high_conf_threshold=0.75,
        low_conf_threshold=0.50
    )

    assert isinstance(audit, CalibrationAuditReport) or audit.__class__.__name__ == "CalibrationAuditReport"
    assert audit.dataset_name == "Indian Pines Hyperspectral AVIRIS Scene"
    assert len(audit.high_confidence_wrong_cases) == 1
    # Check that index 2 was flagged as critical/high severity failure case
    hc_case = audit.high_confidence_wrong_cases[0]
    assert hc_case["severity"] in ["critical", "high"]
    assert "Predicted Class 2" in hc_case["actual_output"]
    assert "Ground Truth Class 0" in hc_case["expected_output"]

    # Check low confidence correct cases
    assert len(audit.low_confidence_correct_cases) == 1
    assert audit.low_confidence_correct_cases[0]["class"] == 1

    # Check worst cases
    assert len(audit.worst_cases) == 2
    assert audit.worst_cases[0]["confidence"] == 0.88


# ==============================================================================
# 10. Integration into EvidencePackage
# ==============================================================================
def test_calibration_integration_evidence_package():
    """Verify VQA evidence engine constructs decomposed uncertainty in ConfidenceCalibrationTraceability."""
    # Synthetic test image
    img = np.random.randint(50, 200, (64, 64, 3), dtype=np.uint8)
    meta = {
        "asset_id": "CAL_SCENE_001",
        "file_path": "tests/data/cal_scene.tif",
        "sensor": "Sentinel-2 MSI",
        "crs": "EPSG:32643",
        "bounds": [72.8, 18.9, 73.0, 19.1],
        "pixel_size_meters": 10.0
    }
    candidates = [
        CandidateAnswer(answer="yes", confidence=0.89),
        CandidateAnswer(answer="no", confidence=0.11)
    ]

    pkg = VQAEvidenceEngine.construct_evidence_package(
        image_arr=img,
        meta=meta,
        query="Is there a runway?",
        top_answer="yes",
        confidence=0.89,
        candidates=candidates,
        is_calibrated=True
    )

    cal_info = pkg.confidence_and_calibration
    assert isinstance(cal_info, ConfidenceCalibrationTraceability) or cal_info.__class__.__name__ == "ConfidenceCalibrationTraceability"
    assert cal_info.confidence_score == 0.89
    assert cal_info.is_calibrated is True
    assert cal_info.confidence_semantics == "probability_class_correctness"
    assert cal_info.aleatoric_uncertainty is not None
    assert cal_info.epistemic_uncertainty is not None
    assert cal_info.data_quality_uncertainty is not None
    assert cal_info.registration_uncertainty == 0.0

