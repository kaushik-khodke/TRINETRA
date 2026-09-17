"""
TRINETRA Stage 8 Test Suite: Unified Benchmark and Evaluation Framework
Governed by 08_STAGE_8_BENCHMARK_FRAMEWORK.md and NON_NEGOTIABLE_PRINCIPLES.md.

Validates:
1. Canonical Benchmark Registry catalog completeness across all specialist domains.
2. Graceful pre-flight dataset validation on missing or incomplete datasets (ZERO DOWNLOADS).
3. Anti-leakage enforcement (disjoint splits and test configuration locking).
4. End-to-end change detection evaluation with real metric computation and bootstrap CIs.
5. End-to-end optical-SAR multimodal fusion evaluation with calibration and failure autopsies.
6. End-to-end hyperspectral evaluation with OA, AA, Kappa, and per-class breakdown.
7. End-to-end RS-VQA evaluation with Top-1, Top-5, Exact Match, and category breakdowns.
8. Statistical 95% empirical bootstrap confidence interval verification.
9. Legitimate Benchmark Comparison Policy enforcement (rejecting incomparable comparisons).
10. Benchmark reporter serialization into machine-readable JSON and publication Markdown.
"""

import os
import sys
import pytest
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from torch.utils.data import DataLoader, TensorDataset

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
project_root = os.path.abspath(os.path.join(backend_root, ".."))
for p in [backend_root, project_root]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from backend.schemas.contracts import BenchmarkRun, BenchmarkMetadata, FailureCase
    from backend.core.exceptions import DataLeakageError
    from backend.evaluation.benchmark_registry import BenchmarkRegistry, default_registry
    from backend.evaluation.runner import (
        UnifiedBenchmarkRunner,
        default_runner,
        compute_expected_calibration_error
    )
    from backend.evaluation.reporter import BenchmarkReporter
    from backend.training.common.metrics import compute_bootstrap_ci_95
except ImportError:
    from schemas.contracts import BenchmarkRun, BenchmarkMetadata, FailureCase
    from core.exceptions import DataLeakageError
    from evaluation.benchmark_registry import BenchmarkRegistry, default_registry
    from evaluation.runner import (
        UnifiedBenchmarkRunner,
        default_runner,
        compute_expected_calibration_error
    )
    from evaluation.reporter import BenchmarkReporter
    from training.common.metrics import compute_bootstrap_ci_95



# ==============================================================================
# 1. Benchmark Registry Catalog Completeness
# ==============================================================================
def test_benchmark_registry_catalog_completeness():
    """Verify default registry contains all canonical remote sensing benchmarks."""
    reg = BenchmarkRegistry()

    expected_benchmarks = [
        "levir_cd",
        "levir_cd_plus",
        "whu_cd",
        "sen12ms",
        "spacenet6",
        "indian_pines",
        "pavia_university",
        "salinas",
        "rsvqa_lr",
        "rsvqa_hr",
        "bigearthnet_s2"
    ]

    for b_id in expected_benchmarks:
        meta = reg.get_benchmark_metadata(b_id)
        assert isinstance(meta, BenchmarkMetadata)
        assert meta.benchmark_id == b_id
        assert len(meta.dataset_name) > 0
        assert len(meta.citation) > 0
        assert meta.task in [
            "change_detection",
            "multimodal_fusion",
            "hyperspectral_classification",
            "vqa",
            "multilabel_landcover"
        ]
        assert len(meta.expected_metrics) > 0

    # Test filtering by task
    cd_bms = reg.list_benchmarks(task="change_detection")
    assert len(cd_bms) >= 3
    assert all(b.task == "change_detection" for b in cd_bms)


# ==============================================================================
# 2. Pre-Flight Validation on Missing Dataset (Zero Downloads Rule)
# ==============================================================================
def test_benchmark_registry_validation_missing_dataset(tmp_path):
    """Verify registry fails gracefully with actionable remediation when data is missing."""
    reg = BenchmarkRegistry()

    non_existent = tmp_path / "non_existent_levir_cd"
    res = reg.validate_dataset_path("levir_cd", non_existent)

    assert res["is_valid"] is False
    assert "Directory not found" in res["error"]
    assert "MANUAL_TRAINING_PROTOCOL.md" in res["remediation"]

    # Verify empty directory triggers incomplete structure
    empty_dir = tmp_path / "empty_dir"
    empty_dir.mkdir()
    res_empty = reg.validate_dataset_path("levir_cd", empty_dir)
    assert res_empty["is_valid"] is False
    assert "missing_elements" in res_empty


# ==============================================================================
# 3. Anti-Leakage Policy Enforcement
# ==============================================================================
def test_anti_leakage_policy_enforcement():
    """Verify split isolation rejects partition leakage and locks test configurations."""
    reg = BenchmarkRegistry()

    # Disjoint splits: should pass
    clean_splits = {
        "train": ["patch_001", "patch_002", "patch_003"],
        "val": ["patch_004"],
        "test": ["patch_005", "patch_006"]
    }
    status = reg.validate_split_isolation(clean_splits)
    assert status["leakage_detected"] is False
    assert status["train_count"] == 3
    assert status["test_count"] == 2

    # Leaking splits: should raise DataLeakageError
    leaking_splits = {
        "train": ["patch_001", "patch_002", "patch_003"],
        "val": ["patch_003"],  # overlap with train
        "test": ["patch_005"]
    }
    with pytest.raises(DataLeakageError):
        reg.validate_split_isolation(leaking_splits)

    # Test configuration locking
    runner = UnifiedBenchmarkRunner(registry=reg)
    cfg1 = {"learning_rate": 0.001, "batch_size": 16}
    h1 = runner.lock_test_configuration("levir_cd", "BIT_Model", cfg1)
    assert len(h1) == 16

    # Re-locking with same config is permitted
    h2 = runner.lock_test_configuration("levir_cd", "BIT_Model", cfg1)
    assert h1 == h2

    # Altering configuration on locked test split raises DataLeakageError
    cfg2 = {"learning_rate": 0.0001, "batch_size": 16}  # changed hyperparameter
    with pytest.raises(DataLeakageError):
        runner.lock_test_configuration("levir_cd", "BIT_Model", cfg2)


# ==============================================================================
# 4. Change Detection Pipeline
# ==============================================================================
class MockChangeModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv = nn.Conv2d(6, 1, kernel_size=1)

    def forward(self, t1, t2):
        x = torch.cat([t1, t2], dim=1)
        return self.conv(x)


def test_unified_runner_change_detection_pipeline():
    """Verify end-to-end evaluation of bi-temporal change detection."""
    runner = UnifiedBenchmarkRunner()
    model = MockChangeModel()

    # Create dummy bitemporal test data
    # 8 samples, 3 channels, 32x32
    t1 = torch.randn(8, 3, 32, 32)
    t2 = torch.randn(8, 3, 32, 32)
    # Ground truth masks with some change pixels
    masks = torch.zeros(8, 1, 32, 32)
    masks[0, 0, 10:20, 10:20] = 1.0
    masks[1, 0, 5:15, 5:15] = 1.0

    dataset = TensorDataset(t1, t2, masks)
    loader = DataLoader(dataset, batch_size=4)

    run = runner.evaluate_change_detection(
        model=model,
        data_loader=loader,
        benchmark_id="levir_cd",
        split="test",
        config={"threshold": 0.5}
    )

    assert isinstance(run, BenchmarkRun)
    assert run.dataset_name == "LEVIR-CD Building Change Detection Benchmark"
    assert run.sample_count == 8
    assert "f1" in run.metrics
    assert "iou" in run.metrics
    assert "precision" in run.metrics
    assert "recall" in run.metrics
    assert run.confidence_interval_95 is not None
    assert "f1" in run.confidence_interval_95
    assert len(run.confidence_interval_95["f1"]) == 2
    assert run.execution_time_seconds >= 0.0
    assert run.provenance_fingerprint is not None


# ==============================================================================
# 5. Optical-SAR Multimodal Fusion Pipeline
# ==============================================================================
class MockOpticalSARModel(nn.Module):
    def __init__(self, num_classes=6):
        super().__init__()
        self.num_classes = num_classes
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(3 + 2, num_classes)

    def forward(self, opt, sar):
        x_opt = self.pool(opt).squeeze(-1).squeeze(-1)
        x_sar = self.pool(sar).squeeze(-1).squeeze(-1)
        feat = torch.cat([x_opt, x_sar], dim=1)
        return self.fc(feat)


def test_unified_runner_optical_sar_pipeline():
    """Verify end-to-end evaluation of Optical-SAR multimodal fusion."""
    runner = UnifiedBenchmarkRunner()
    model = MockOpticalSARModel(num_classes=6)

    # 12 samples: optical (3, 16, 16), SAR (2, 16, 16), targets (0 to 5)
    opt = torch.randn(12, 3, 16, 16)
    sar = torch.randn(12, 2, 16, 16)
    targets = torch.tensor([0, 1, 2, 3, 4, 5, 0, 1, 2, 3, 4, 5], dtype=torch.long)

    dataset = TensorDataset(opt, sar, targets)
    loader = DataLoader(dataset, batch_size=4)

    run = runner.evaluate_multimodal_fusion(
        model=model,
        data_loader=loader,
        benchmark_id="sen12ms",
        split="test",
        num_classes=6,
        config={"fusion_method": "concat"}
    )

    assert isinstance(run, BenchmarkRun)
    assert run.dataset_name == "SEN12MS Multi-Sensor Earth Observation Archive"
    assert run.sample_count == 12
    assert "overall_accuracy" in run.metrics
    assert "kappa_coefficient" in run.metrics
    assert "macro_f1" in run.metrics
    assert run.per_class_metrics is not None
    assert len(run.per_class_metrics) == 6
    assert "overall_accuracy" in run.confidence_interval_95
    assert run.calibration_metrics is not None
    assert "ece" in run.calibration_metrics


# ==============================================================================
# 6. Hyperspectral Specialist Pipeline
# ==============================================================================
class MockHyperspectralModel(nn.Module):
    def __init__(self, in_bands=10, num_classes=16):
        super().__init__()
        self.net = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(in_bands, num_classes)
        )

    def forward(self, cube):
        return self.net(cube)


def test_unified_runner_hyperspectral_pipeline():
    """Verify end-to-end evaluation of hyperspectral classification."""
    runner = UnifiedBenchmarkRunner()
    model = MockHyperspectralModel(in_bands=10, num_classes=16)

    # 16 samples: cubes (10 bands, 7, 7), labels (0 to 15)
    cubes = torch.randn(16, 10, 7, 7)
    labels = torch.tensor(list(range(16)), dtype=torch.long)

    dataset = TensorDataset(cubes, labels)
    loader = DataLoader(dataset, batch_size=8)

    run = runner.evaluate_hyperspectral(
        model=model,
        data_loader=loader,
        benchmark_id="indian_pines",
        split="test",
        num_classes=16,
        config={"block_size": 16}
    )

    assert isinstance(run, BenchmarkRun)
    assert run.dataset_name == "Indian Pines Hyperspectral AVIRIS Scene"
    assert run.sample_count == 16
    assert "overall_accuracy" in run.metrics
    assert "average_accuracy" in run.metrics
    assert "macro_f1" in run.metrics
    assert run.per_class_metrics is not None
    assert len(run.per_class_metrics) == 16


# ==============================================================================
# 7. Remote Sensing VQA Pipeline
# ==============================================================================
class MockVQAModel(nn.Module):
    def __init__(self, vocab_size=20, num_answers=10):
        super().__init__()
        self.num_answers = num_answers
        self.fc = nn.Linear(3 + vocab_size, num_answers)

    def forward(self, img, token_ids):
        img_f = img.mean(dim=[2, 3])
        tok_f = token_ids.float()
        feat = torch.cat([img_f, tok_f], dim=1)
        return self.fc(feat)


def test_unified_runner_vqa_pipeline():
    """Verify end-to-end RS-VQA evaluation with question category breakdowns."""
    runner = UnifiedBenchmarkRunner()
    model = MockVQAModel(vocab_size=8, num_answers=5)

    # 10 samples
    imgs = torch.randn(10, 3, 16, 16)
    tokens = torch.randint(0, 5, (10, 8))
    targets = torch.tensor([0, 1, 2, 3, 4, 0, 1, 2, 3, 4], dtype=torch.long)

    questions = [
        "Is there a building?",
        "How many airplanes are visible?",
        "Are there more trees than roads?",
        "What is the area covered by water?",
        "Is there a runway?",
        "How many ships are docked?",
        "Is there greater vegetation than bare soil?",
        "What is the size of the sports field?",
        "Is there a river present?",
        "How many storage tanks are present?"
    ]

    idx2ans = {0: "yes", 1: "no", 2: "3", 3: "500 m2", 4: "trees"}

    batch = {
        "images": imgs,
        "token_ids": tokens,
        "targets": targets,
        "questions": questions
    }
    loader = [batch]

    run = runner.evaluate_vqa(
        model=model,
        data_loader=loader,
        benchmark_id="rsvqa_lr",
        split="test",
        idx2ans=idx2ans,
        config={"vocab_size": 8}
    )

    assert isinstance(run, BenchmarkRun)
    assert run.dataset_name == "RSVQA Low Resolution Benchmark"
    assert run.sample_count == 10
    assert "top1_accuracy" in run.metrics
    assert "top5_accuracy" in run.metrics
    assert "exact_match" in run.metrics
    assert "category_presence_accuracy" in run.metrics
    assert "category_count_accuracy" in run.metrics


# ==============================================================================
# 8. Statistical Bootstrap Confidence Interval Verification
# ==============================================================================
def test_statistical_bootstrap_confidence_intervals():
    """Verify empirical 95% bootstrap confidence interval estimation."""
    # Deterministic test array
    np.random.seed(42)
    sample_scores = np.random.normal(loc=0.85, scale=0.04, size=100)

    lower, upper = compute_bootstrap_ci_95(sample_scores, n_bootstraps=300, seed=42)

    assert lower < upper
    assert 0.80 <= lower <= 0.86
    assert 0.84 <= upper <= 0.90
    assert (upper - lower) > 0.005


# ==============================================================================
# 9. Legitimate Benchmark Comparison Policy
# ==============================================================================
def test_comparison_policy_compatibility_checks():
    """Verify that compare_benchmark_runs rejects incomparable runs and compares valid runs."""
    run_base = BenchmarkRun(
        benchmark_id="run_001",
        dataset_name="LEVIR-CD Building Change Detection Benchmark",
        dataset_manifest_hash="hash_alpha_12345",
        split="test",
        sample_count=100,
        metrics={"f1": 0.8520, "iou": 0.7422, "precision": 0.8710, "recall": 0.8340},
        execution_time_seconds=12.5,
        model_name="SiameseUNetBaseline"
    )

    run_cand = BenchmarkRun(
        benchmark_id="run_002",
        dataset_name="LEVIR-CD Building Change Detection Benchmark",
        dataset_manifest_hash="hash_alpha_12345",
        split="test",
        sample_count=100,
        metrics={"f1": 0.8910, "iou": 0.8035, "precision": 0.9050, "recall": 0.8770},
        execution_time_seconds=14.2,
        model_name="BitemporalInteractionTransformer"
    )

    # Valid comparison
    comp = BenchmarkReporter.compare_benchmark_runs(run_base, run_cand)
    assert comp["dataset_name"] == "LEVIR-CD Building Change Detection Benchmark"
    assert "f1" in comp["metrics"]
    assert comp["metrics"]["f1"]["statistically_higher"] == "run_b"
    assert comp["metrics"]["f1"]["absolute_diff"] == pytest.approx(0.0390, abs=1e-4)
    assert "| Baseline (Run A) | Candidate (Run B) |" in comp["markdown_table"]

    # Incompatible dataset: must raise ValueError
    run_diff_dataset = run_cand.model_copy(update={"dataset_name": "WHU Building Change Detection Dataset"})
    with pytest.raises(ValueError, match="Incompatible datasets"):
        BenchmarkReporter.compare_benchmark_runs(run_base, run_diff_dataset)

    # Incompatible split: must raise ValueError
    run_diff_split = run_cand.model_copy(update={"split": "val"})
    with pytest.raises(ValueError, match="Split mismatch"):
        BenchmarkReporter.compare_benchmark_runs(run_base, run_diff_split)


# ==============================================================================
# 10. Benchmark Reporter Serialization
# ==============================================================================
def test_benchmark_reporter_markdown_and_json_serialization(tmp_path):
    """Verify Markdown report generation and file persistence."""
    run = BenchmarkRun(
        benchmark_id="run_audit_999",
        dataset_name="LEVIR-CD Building Change Detection Benchmark",
        dataset_manifest_hash="sha256_mock_hash",
        split="test",
        sample_count=50,
        metrics={"f1": 0.8850, "iou": 0.7930, "precision": 0.9010, "recall": 0.8700},
        confidence_interval_95={"f1": [0.8650, 0.9020], "iou": [0.7710, 0.8140]},
        calibration_metrics={"ece": 0.0450},
        execution_time_seconds=8.45,
        model_name="BIT_Model",
        failures_count=1,
        failure_cases=[{
            "case_id": "fc_01",
            "failure_type": "false_negative",
            "severity": "medium",
            "confidence_score": 0.72,
            "root_cause_analysis": "Roof spectral variation"
        }],
        limitations=["Shadow sensitivity"]
    )

    # Generate Markdown
    md = BenchmarkReporter.generate_markdown_report(run)
    assert "# Benchmark Evaluation Audit Report: LEVIR-CD" in md
    assert "**Evaluated Split**: `TEST`" in md
    assert "[0.8650, 0.9020]" in md
    assert "Roof spectral variation" in md
    assert "Shadow sensitivity" in md

    # Save outputs to disk
    out_files = BenchmarkReporter.save_report(run, tmp_path)
    assert Path(out_files["json_path"]).is_file()
    assert Path(out_files["markdown_path"]).is_file()

    # Verify JSON content
    with open(out_files["json_path"], "r") as f:
        content = f.read()
        assert "run_audit_999" in content
        assert "LEVIR-CD Building Change Detection Benchmark" in content
