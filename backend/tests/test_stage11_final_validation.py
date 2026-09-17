"""
TRINETRA Stage 11 Final Judge-Facing Validation Test Suite
Governed by 11_STAGE_11_FINAL_VALIDATION.md and NON_NEGOTIABLE_PRINCIPLES.md.

Tests:
1. Judge-Facing Wording & Claims Compliance (Detecting forbidden marketing, approving scientific rigor)
2. Indian EO & ISRO Relevance Validation (Strict non-ground-truth labeling, geometric/radiometric sanity)
3. Failure Evidence Taxonomy (All 7 required technical defense categories)
4. Final Release Gate (8-point criteria verification, certification vs rejection)
5. Judge-Facing Submission Package Builder (Complete 8-document generation + checksummed manifest)
"""

import os
import sys
import json
import pytest
import numpy as np
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evaluation.judge_wording import JudgeFacingGlossary, ComplianceAuditResult, WordingViolation
from geospatial.indian_eo import (
    IndianEOSensor,
    ReferenceLabelType,
    IndianEOScene,
    IndianEOCatalog,
    IndianEOValidator,
    IndianEOValidationReport
)
from evaluation.final_validation import (
    FailureTaxonomy,
    ReleaseGateCheck,
    ReleaseGateStatus,
    FinalValidationPipeline
)
from evaluation.submission_builder import SubmissionPackageBuilder, compute_file_sha256
from core.reproducibility import create_reproducibility_bundle
from schemas.contracts import BenchmarkRun


# =========================================================================
# 1. Judge-Facing Wording & Compliance Tests
# =========================================================================

def test_judge_wording_detects_forbidden_claims():
    """Detects forbidden marketing hype, uncalibrated claims, and fake certifications."""
    forbidden_text = """
    Our system is always correct in identifying all building changes.
    The neural network is ISRO-certified for operational deployment.
    We achieved absolute SOTA across all satellite benchmarks.
    This unannotated Cartosat scene is our ground truth.
    Our 94% confidence means 94% correct detections.
    """
    audit = JudgeFacingGlossary.audit_text(forbidden_text)

    assert not audit.is_compliant
    assert audit.total_violations >= 4
    assert audit.compliance_score < 1.0

    matched_rules = [v.reason for v in audit.violations]
    assert any("Absolute accuracy" in r for r in matched_rules)
    assert any("certified" in r.lower() for r in matched_rules)
    assert any("Unqualified SOTA" in r for r in matched_rules)
    assert any("Unannotated satellite rasters" in r for r in matched_rules)


def test_judge_wording_approves_rigorous_scientific_claims():
    """Approves compliant, rigorous scientific formulations."""
    approved_text = """
    # Technical Defense
    Independently benchmarked against published ground-truth datasets using reproducible evaluation protocols.
    Empirically evaluated on canonical test partitions with 95% bootstrap confidence intervals.
    Predictive uncertainty quantified via Expected Calibration Error (ECE) and post-hoc temperature scaling.
    Evaluated on Indian Earth Observation rasters for geometric and radiometric consistency; 
    unannotated sensor data is not labeled as authoritative ground truth.
    Predictions are subject to sensor resolution boundaries, atmospheric interference, and coregistration tolerances.
    """
    audit = JudgeFacingGlossary.audit_text(approved_text)

    assert audit.is_compliant
    assert audit.total_violations == 0
    assert audit.compliance_score == 1.0


def test_judge_wording_sanitizer():
    """Automatically replaces forbidden phrases with compliant scientific equivalents."""
    raw_text = "Our model is always correct and achieves SOTA on unannotated raw bhuvan ground truth."
    sanitized = JudgeFacingGlossary.sanitize_text(raw_text)

    assert "always correct" not in sanitized
    assert "empirically characterized" in sanitized
    assert "ground truth" not in sanitized


# =========================================================================
# 2. Indian EO / ISRO Relevance Validation Tests
# =========================================================================

def test_indian_eo_scene_catalog_integrity():
    """Verifies catalog contains canonical Indian EO platforms within Indian territorial bounds."""
    scenes = IndianEOCatalog.list_scenes()
    assert len(scenes) >= 4

    scene_ids = [s.scene_id for s in scenes]
    assert "ISRO_HYD_LISS4_2023" in scene_ids
    assert "ISRO_MUM_RISAT1_2022" in scene_ids
    assert "ISRO_THAR_AWIFS_2023" in scene_ids

    for scene in scenes:
        min_lon, min_lat, max_lon, max_lat = scene.geographic_bounds
        # Must be within Indian geographic bounding envelope
        assert 68.0 <= min_lon < max_lon <= 98.0
        assert 6.0 <= min_lat < max_lat <= 38.0
        assert scene.spatial_resolution_meters > 0


def test_indian_eo_rejects_false_ground_truth_labeling():
    """Guarantees Non-Negotiable Principle #11: Unannotated data is NEVER called ground truth."""
    liss4 = IndianEOCatalog.get_scene("ISRO_HYD_LISS4_2023")
    assert liss4 is not None
    assert liss4.reference_type == ReferenceLabelType.UNANNOTATED_SENSOR_DATA
    assert not liss4.is_true_ground_truth()

    proxy_scene = IndianEOCatalog.get_scene("NRSC_BHUVAN_URBAN_PROXY")
    assert proxy_scene is not None
    assert proxy_scene.reference_type == ReferenceLabelType.SENSOR_DERIVED_PROXY
    assert not proxy_scene.is_true_ground_truth()


def test_indian_eo_validator_geometric_and_radiometric():
    """Tests geometric bounding sanity, radiometric dynamic range, and domain shift."""
    scene = IndianEOCatalog.get_scene("ISRO_HYD_LISS4_2023")
    assert scene is not None

    # Healthy synthetic raster (3 bands, 64x64, mean variance)
    np.random.seed(42)
    raster = np.random.uniform(0.1, 0.9, size=(3, 64, 64)).astype(np.float32)
    predictions = np.random.uniform(0.2, 0.8, size=(64, 64)).astype(np.float32)

    report = IndianEOValidator.validate_scene(scene, raster, predictions)

    assert report.geometric_sanity_pass
    assert report.radiometric_sanity_pass
    assert report.domain_shift_uncertainty_score > 0.0
    assert "NOT labeled as authoritative ground truth" in report.disclaimer
    assert "Unannotated Sensor Imagery" in report.authoritative_label_status


def test_indian_eo_validator_detects_corrupted_raster():
    """Detects all-zero or corrupted nodata rasters."""
    scene = IndianEOCatalog.get_scene("ISRO_HYD_LISS4_2023")
    assert scene is not None

    # All-zero corrupted raster
    zero_raster = np.zeros((3, 64, 64), dtype=np.float32)
    report = IndianEOValidator.validate_scene(scene, zero_raster)

    assert not report.radiometric_sanity_pass


# =========================================================================
# 3. Failure Evidence Taxonomy Tests (All 7 Categories)
# =========================================================================

def test_final_validation_failure_taxonomy_populates_all_seven_categories():
    """Verifies that all 7 required failure/success categories are accurately mined."""
    pipeline = FinalValidationPipeline()

    preds = np.array([1, 1, 0, 1, 1, 0, 1, 0])
    targs = np.array([1, 0, 1, 0, 1, 1, 0, 1])
    confs = np.array([0.95, 0.88, 0.60, 0.52, 0.45, 0.70, 0.40, 0.65])
    meta = [
        {"quality_flags": []},                                         # 0: Success (1==1)
        {"quality_flags": []},                                         # 1: High-confidence failure (1!=0, conf=0.88 >= 0.75)
        {"quality_flags": ["REGISTRATION_OFFSET_1.2PX"]},             # 2: Registration failure
        {"quality_flags": ["CLOUD_SHADOW_COVERAGE"]},                 # 3: Cloud / Seasonal failure
        {"quality_flags": ["SENSOR_NOISE_STRIPING"]},                 # 4: Success with noise flag
        {"quality_flags": ["SATURATION_SPIKE"]},                      # 5: Low-quality input failure
        {"quality_flags": []},                                         # 6: False positive (p=1, t=0, conf=0.40)
        {"quality_flags": []},                                         # 7: False negative (p=0, t=1, conf=0.65)
    ]

    taxonomy = pipeline.collect_failure_evidence(preds, targs, confs, meta)

    assert len(taxonomy.success_examples) >= 2
    assert len(taxonomy.high_confidence_failures) >= 1
    assert len(taxonomy.registration_failures) >= 1
    assert len(taxonomy.cloud_season_failures) >= 1
    assert len(taxonomy.low_quality_input_cases) >= 1
    assert len(taxonomy.false_positives) >= 1
    assert len(taxonomy.false_negatives) >= 1
    assert taxonomy.total_cases() == 8


# =========================================================================
# 4. Final Release Gate Tests (8-point criteria)
# =========================================================================

def _create_mock_benchmark_run(dataset_name: str, primary_metric: float, ece: float) -> BenchmarkRun:
    """Helper to create a fully specified BenchmarkRun for gating tests."""
    return BenchmarkRun(
        benchmark_id=f"run_{dataset_name.lower()}",
        dataset_name=dataset_name,
        dataset_manifest_hash="a1b2c3d4e5f67890",
        split="test",
        sample_count=1000,
        metrics={"iou": primary_metric, "f1": 0.85},
        confidence_interval_95={"iou": [primary_metric - 0.02, primary_metric + 0.02]},
        calibration_metrics={"ece": ece, "mce": ece * 1.5, "brier_score": 0.08},
        execution_time_seconds=1.23,
        model_name="CanonicalSpecialistModel",
        provenance_fingerprint="fp_canonical_123"
    )


def test_final_release_gate_passes_when_all_criteria_met():
    """Certifies production readiness when all 8 criteria pass."""
    pipeline = FinalValidationPipeline()

    benchmarks = [
        _create_mock_benchmark_run("LEVIR-CD", 0.812, 0.038),
        _create_mock_benchmark_run("SEN12MS", 0.785, 0.029),
        _create_mock_benchmark_run("Indian_Pines", 0.942, 0.041),
        _create_mock_benchmark_run("RSVQA_LR", 0.814, 0.034)
    ]

    # Provide taxonomy with all 7 categories populated
    taxonomy = FailureTaxonomy(
        success_examples=[{"case_id": "c1"}],
        false_positives=[{"case_id": "c2"}],
        false_negatives=[{"case_id": "c3"}],
        registration_failures=[{"case_id": "c4"}],
        cloud_season_failures=[{"case_id": "c5"}],
        low_quality_input_cases=[{"case_id": "c6"}],
        high_confidence_failures=[{"case_id": "c7"}]
    )

    clean_docs = [
        "Independently benchmarked against published ground-truth datasets using reproducible protocols.",
        "Empirically evaluated on canonical test partitions with 95% bootstrap confidence intervals."
    ]

    gate = pipeline.evaluate_final_release_gate(
        benchmark_runs=benchmarks,
        failure_taxonomy=taxonomy,
        text_documents=clean_docs,
        security_passed=True,
        fallbacks_transparent=True
    )

    assert gate.certified_production_ready
    assert gate.gate_verdict == "CERTIFIED_FOR_SUBMISSION"
    assert gate.passed_count == 8
    assert len(gate.rejection_reasons) == 0


def test_final_release_gate_rejects_when_criterion_fails():
    """Rejects at gate if forbidden wording, missing calibration, or missing failures occur."""
    pipeline = FinalValidationPipeline()

    # Benchmark lacking calibration metrics
    bad_benchmark = BenchmarkRun(
        benchmark_id="run_bad",
        dataset_name="LEVIR-CD",
        dataset_manifest_hash="hash123",
        split="test",
        sample_count=500,
        metrics={"iou": 0.80},
        execution_time_seconds=0.85,
        calibration_metrics=None  # Missing calibration!
    )

    empty_taxonomy = FailureTaxonomy()  # Incomplete failure evidence

    hype_docs = ["Our AI is always correct and ISRO-certified!"]

    gate = pipeline.evaluate_final_release_gate(
        benchmark_runs=[bad_benchmark],
        failure_taxonomy=empty_taxonomy,
        text_documents=hype_docs,
        security_passed=False,
        fallbacks_transparent=False
    )

    assert not gate.certified_production_ready
    assert gate.gate_verdict == "REJECTED_AT_GATE"
    assert len(gate.rejection_reasons) >= 4
    reasons_str = " ".join(gate.rejection_reasons).lower()
    assert "calibration" in reasons_str
    assert "failure evidence incomplete" in reasons_str
    assert "non-compliant" in reasons_str
    assert "security" in reasons_str


# =========================================================================
# 5. Submission Package Builder Tests
# =========================================================================

def test_submission_package_builder_builds_complete_bundle(tmp_path):
    """Verifies that all 8 documents and submission_manifest.json are generated and compliant."""
    builder = SubmissionPackageBuilder(output_dir=str(tmp_path))

    benchmarks = [
        _create_mock_benchmark_run("LEVIR-CD", 0.812, 0.038),
        _create_mock_benchmark_run("SEN12MS", 0.785, 0.029),
        _create_mock_benchmark_run("Indian_Pines", 0.942, 0.041),
        _create_mock_benchmark_run("RSVQA_LR", 0.814, 0.034)
    ]

    scene = IndianEOCatalog.get_scene("ISRO_HYD_LISS4_2023")
    dummy_raster = np.random.uniform(0.1, 0.9, size=(3, 32, 32)).astype(np.float32)
    report = IndianEOValidator.validate_scene(scene, dummy_raster)

    taxonomy = FailureTaxonomy(
        success_examples=[{"case_id": "c1", "predicted": 1, "confidence": 0.95}],
        false_positives=[{"case_id": "c2", "predicted": 1, "ground_truth": 0, "confidence": 0.65}],
        false_negatives=[{"case_id": "c3", "predicted": 0, "ground_truth": 1, "confidence": 0.70}],
        registration_failures=[{"case_id": "c4"}],
        cloud_season_failures=[{"case_id": "c5"}],
        low_quality_input_cases=[{"case_id": "c6"}],
        high_confidence_failures=[{"case_id": "c7"}]
    )

    bundle = create_reproducibility_bundle(
        run_id="submission_run_01",
        checkpoint_hash="chk_sha256_mock_123",
        dataset_manifest_hash="mnf_sha256_mock_456"
    )

    gate_status = ReleaseGateStatus(
        certified_production_ready=True,
        gate_verdict="CERTIFIED_FOR_SUBMISSION",
        passed_count=8,
        total_criteria=8,
        checks=[]
    )

    generated = builder.build_package(
        gate_status=gate_status,
        benchmark_runs=benchmarks,
        indian_reports=[report],
        failure_taxonomy=taxonomy,
        reproducibility_bundle=bundle
    )

    expected_files = [
        "00_EXECUTIVE_SUMMARY.md",
        "01_BENCHMARK_EVIDENCE.md",
        "02_INDIAN_EO_VALIDATION.md",
        "03_CALIBRATION_AND_UNCERTAINTY.md",
        "04_FAILURE_AUTOPSIES.md",
        "05_REPRODUCIBILITY_AUDIT.md",
        "06_SECURITY_AND_HARDENING.md",
        "07_LIMITATIONS_AND_ETHICS.md",
        "submission_manifest.json"
    ]

    for fname in expected_files:
        assert fname in generated
        fpath = Path(generated[fname])
        assert fpath.exists()
        assert fpath.stat().st_size > 0

    # Verify manifest structure
    manifest_path = Path(generated["submission_manifest.json"])
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    assert manifest_data["problem_statement"] == "26167"
    assert manifest_data["gate_certification"]["certified_production_ready"]
    assert len(manifest_data["documents"]) == 8

    # Verify that all generated markdown documents pass judge-wording audit
    for fname in expected_files:
        if fname.endswith(".md"):
            with open(Path(generated[fname]), "r", encoding="utf-8") as f:
                content = f.read()
            audit = JudgeFacingGlossary.audit_text(content)
            assert audit.is_compliant, f"{fname} failed judge wording audit: {audit.violations}"
