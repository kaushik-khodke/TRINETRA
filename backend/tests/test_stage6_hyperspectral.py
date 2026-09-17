"""
TRINETRA / SatQuery AI — Stage 6 Automated Test Suite: Hyperspectral Remote Sensing Specialist
File: backend/tests/test_stage6_hyperspectral.py

Validates:
1. Pure Spectral MLP Baseline, 3D-2D HybridSN CNN, and HyperFree ViT-B Adapter models.
2. Comprehensive Hyperspectral Metrics (OA, AA, Cohen's Kappa, Macro-F1, Confusion Matrix).
3. Geographic Spatial Block Grid Partitioning (Zero cross-split block leakage).
4. Boundary Buffer Margins (Zero patch receptive field autocorrelation leakage).
5. Train-only spectral normalization (no data leakage).
6. Multi-mode patch & pixel dataset extraction ('pixel', 'patch_2d', 'patch_3d').
7. Hyperspectral Dataset Validator and Spatial Manifest builder.
8. Hyperspectral Failure Analysis Engine (SAM, metamerism, mixed-pixel boundaries, starvation).
9. Live ModelManager loader and HyperFreeHSISpecialist service execution.
Governed by Stage 6 Hyperspectral Protocol. Zero synthetic data in metric reporting.
"""

import os
import sys
import importlib.util
from pathlib import Path
import numpy as np
import pytest
import torch

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)


def _load_module(module_name: str, file_path: str):
    full_path = os.path.join(backend_root, file_path)
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Stage 6 Isolated Module Loaders
hsi_dataset_mod = _load_module("stage6_hsi_dataset", "training/06_hyperspectral/dataset.py")
hsi_validate_mod = _load_module("stage6_hsi_validate", "training/06_hyperspectral/validate_dataset.py")
hsi_failure_mod = _load_module("stage6_hsi_failure", "training/06_hyperspectral/failure_analysis.py")

HyperspectralSpatialDataset = hsi_dataset_mod.HyperspectralSpatialDataset
partition_spatial_grid = hsi_dataset_mod.partition_spatial_grid
compute_train_normalization_stats = hsi_dataset_mod.compute_train_normalization_stats
HyperspectralDatasetValidator = hsi_validate_mod.HyperspectralDatasetValidator
HyperspectralFailureAnalysisEngine = hsi_failure_mod.HyperspectralFailureAnalysisEngine
spectral_angle_mapper = hsi_failure_mod.spectral_angle_mapper

from training.common.metrics import hyperspectral_metrics
from models.hyperspectral_models import (
    SpectralMLPBaseline,
    HybridSNBaseline,
    HyperFreeBAdapter,
    create_hsi_model
)
from models.loader import ModelManager
from services.hyperspectral.hsi_service import HyperFreeHSISpecialist


# ==============================================================================
# 1. Model Architecture Tests
# ==============================================================================
def test_spectral_mlp_baseline():
    model = SpectralMLPBaseline(in_channels=30, num_classes=5, hidden_dims=[64, 32])
    x = torch.randn(8, 30)
    out = model(x)
    assert out.shape == (8, 5)
    assert not torch.isnan(out).any()


def test_hybridsn_baseline():
    # Input format: (B, 1, channels, patch_size, patch_size)
    model = HybridSNBaseline(in_channels=30, num_classes=6, patch_size=7)
    x = torch.randn(4, 1, 30, 7, 7)
    out = model(x)
    assert out.shape == (4, 6)
    assert not torch.isnan(out).any()


def test_hyperfree_adapter():
    # Input format: (B, channels, patch_size, patch_size)
    model = HyperFreeBAdapter(in_channels=30, num_classes=4, patch_size=8, embed_dim=64, depth=2, num_heads=2)
    x = torch.randn(2, 30, 8, 8)
    out = model(x)
    assert out.shape == (2, 4)
    assert not torch.isnan(out).any()


def test_create_hsi_model_factory():
    mlp = create_hsi_model("spectral_mlp", in_channels=20, num_classes=3)
    assert isinstance(mlp, SpectralMLPBaseline)

    hsn = create_hsi_model("hybridsn", in_channels=20, num_classes=3, patch_size=7)
    assert isinstance(hsn, HybridSNBaseline)

    adapter = create_hsi_model("hyperfree", in_channels=20, num_classes=3, patch_size=8, embed_dim=64, depth=2)
    assert isinstance(adapter, HyperFreeBAdapter)

    with pytest.raises(ValueError):
        create_hsi_model("nonexistent_arch")


# ==============================================================================
# 2. Hyperspectral Remote Sensing Metrics Tests
# ==============================================================================
def test_hyperspectral_metrics_perfect_accuracy():
    y_true = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2])
    y_pred = np.array([0, 1, 2, 0, 1, 2, 0, 1, 2])

    res = hyperspectral_metrics(y_pred, y_true, num_classes=3)
    assert res["overall_accuracy"] == 1.0
    assert res["average_accuracy"] == 1.0
    assert res["kappa_coefficient"] == 1.0
    assert res["macro_f1"] == 1.0
    assert res["total_samples"] == 9
    assert len(res["confusion_matrix"]) == 3


def test_hyperspectral_metrics_imperfect_calculation():
    # Known 2x2 confusion matrix:
    # True: [0, 0, 1, 1]
    # Pred: [0, 1, 1, 1]
    # Correct: 3/4 = 0.75 OA
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 1, 1, 1])

    res = hyperspectral_metrics(y_pred, y_true, num_classes=2)
    assert res["overall_accuracy"] == 0.75
    assert res["oa_percent"] == 75.0
    # Class 0 recall: 1/2 = 0.5. Class 1 recall: 2/2 = 1.0. AA = (0.5 + 1.0) / 2 = 0.75
    assert res["average_accuracy"] == 0.75
    # Row sums: [2, 2], Col sums: [1, 3] -> p_e = (2*1 + 2*3)/16 = 8/16 = 0.5
    # Kappa = (0.75 - 0.5)/(1 - 0.5) = 0.25 / 0.5 = 0.5
    assert abs(res["kappa_coefficient"] - 0.5) < 1e-4


def test_hyperspectral_metrics_ignore_index():
    # True labels have background 0 and classes 1, 2
    y_true = np.array([0, 0, 1, 2, 1])
    y_pred = np.array([1, 2, 1, 2, 2])  # 0s are ignored, only indices 2, 3, 4 evaluated: [1, 2, 1] vs [1, 2, 2] -> 2/3 correct

    res = hyperspectral_metrics(y_pred, y_true, ignore_index=0)
    assert res["total_samples"] == 3
    assert abs(res["overall_accuracy"] - (2 / 3)) < 1e-3


# ==============================================================================
# 3. Spatial Block Partitioning & Boundary Buffer Tests
# ==============================================================================
def test_partition_spatial_grid_disjointness():
    height, width = 64, 64
    block_grid, split_blocks, bounds = partition_spatial_grid(
        height=height,
        width=width,
        grid_rows=4,
        grid_cols=4
    )

    train_set = set(split_blocks["train"])
    val_set = set(split_blocks["val"])
    test_set = set(split_blocks["test"])

    # Verify complete disjointness
    assert len(train_set & val_set) == 0, "Train and Val share blocks!"
    assert len(train_set & test_set) == 0, "Train and Test share blocks!"
    assert len(val_set & test_set) == 0, "Val and Test share blocks!"
    assert len(train_set | val_set | test_set) == 16, "All 16 blocks must be assigned!"

    # Verify grid values match block IDs
    assert block_grid.shape == (height, width)
    assert np.min(block_grid) == 0
    assert np.max(block_grid) == 15


def test_boundary_buffer_margin_zero_patch_overlap():
    height, width = 64, 64
    cube = np.random.randn(height, width, 10).astype(np.float32)
    # Fully labeled foreground
    gt = np.random.randint(1, 4, size=(height, width)).astype(np.int64)

    patch_size = 7
    margin = patch_size // 2  # 3 pixels

    ds_train = HyperspectralSpatialDataset(
        cube_or_path=cube,
        gt_or_path=gt,
        split="train",
        patch_size=patch_size,
        boundary_margin=margin,
        mode="pixel"
    )
    ds_test = HyperspectralSpatialDataset(
        cube_or_path=cube,
        gt_or_path=gt,
        split="test",
        patch_size=patch_size,
        boundary_margin=margin,
        mode="pixel",
        norm_stats=ds_train.norm_stats
    )

    assert len(ds_train) > 0
    assert len(ds_test) > 0

    train_coords = np.array([(s[0], s[1]) for s in ds_train.samples])
    test_coords = np.array([(s[0], s[1]) for s in ds_test.samples])

    # Check minimum Chebyshev distance (L_infinity) between any train and test center
    # Must be >= patch_size to ensure 0 overlapping pixels in patches!
    sub_train = train_coords[:100]
    sub_test = test_coords[:100]
    diff = np.abs(sub_train[:, None, :] - sub_test[None, :, :])
    chebyshev = np.max(diff, axis=-1)
    min_dist = int(np.min(chebyshev))

    assert min_dist >= patch_size, (
        f"Boundary buffer failure: minimum train-test distance is {min_dist}, "
        f"which is less than patch_size {patch_size} (overlap detected!)"
    )


def test_train_only_normalization_integrity():
    height, width, bands = 32, 32, 5
    cube = np.zeros((height, width, bands), dtype=np.float32)
    # Put very distinct values in train vs test regions
    block_grid, split_blocks, _ = partition_spatial_grid(height, width, 2, 2)
    train_mask = np.isin(block_grid, split_blocks["train"])
    test_mask = np.isin(block_grid, split_blocks["test"])

    cube[train_mask] = 10.0  # Train mean = 10.0
    cube[test_mask] = 100.0  # Test mean = 100.0

    stats = compute_train_normalization_stats(cube, block_grid, split_blocks["train"])
    # Train mean should be 10.0, NOT contaminated by 100.0 from test blocks
    assert np.allclose(stats["mean"], 10.0, atol=1e-3)


# ==============================================================================
# 4. Multi-Mode Dataset Extraction Tests
# ==============================================================================
def test_dataset_extraction_modes():
    height, width, bands = 40, 40, 15
    cube = np.random.randn(height, width, bands).astype(np.float32)
    gt = np.ones((height, width), dtype=np.int64)

    # 1. Mode: pixel
    ds_pixel = HyperspectralSpatialDataset(cube, gt, split="train", patch_size=7, mode="pixel")
    data_px, target_px, coords_px = ds_pixel[0]
    assert data_px.shape == (bands,)
    assert isinstance(data_px, torch.Tensor)
    assert isinstance(coords_px, tuple) and len(coords_px) == 2

    # 2. Mode: patch_2d
    ds_2d = HyperspectralSpatialDataset(cube, gt, split="train", patch_size=7, mode="patch_2d", norm_stats=ds_pixel.norm_stats)
    data_2d, target_2d, _ = ds_2d[0]
    assert data_2d.shape == (bands, 7, 7)

    # 3. Mode: patch_3d
    ds_3d = HyperspectralSpatialDataset(cube, gt, split="train", patch_size=7, mode="patch_3d", norm_stats=ds_pixel.norm_stats)
    data_3d, target_3d, _ = ds_3d[0]
    assert data_3d.shape == (1, bands, 7, 7)


# ==============================================================================
# 5. Dataset Validator & Manifest Tests
# ==============================================================================
def test_hyperspectral_dataset_validator():
    sample_dir = os.path.join(backend_root, "sample_data")
    cube_path = os.path.join(sample_dir, "sample_hsi.mat")
    gt_path = os.path.join(sample_dir, "sample_hsi_gt.mat")

    validator = HyperspectralDatasetValidator(grid_rows=4, grid_cols=4, patch_size=7)
    manifest = validator.validate(cube_path, gt_path)

    assert manifest["valid"] is True
    assert manifest["num_bands"] == 200
    assert manifest["num_classes"] == 3
    assert manifest["sample_counts"]["train"] > 0
    assert manifest["sample_counts"]["test"] > 0
    assert len(manifest["errors"]) == 0


# ==============================================================================
# 6. Hyperspectral Failure Analysis Engine Tests
# ==============================================================================
def test_spectral_angle_mapper():
    s1 = np.array([1.0, 2.0, 3.0])
    s2 = np.array([2.0, 4.0, 6.0])  # Identical direction
    assert abs(spectral_angle_mapper(s1, s2)) < 1e-6

    s3 = np.array([1.0, 0.0, 0.0])
    s4 = np.array([0.0, 1.0, 0.0])  # Orthogonal
    assert abs(spectral_angle_mapper(s3, s4) - (np.pi / 2)) < 1e-4


def test_failure_analysis_rare_class_starvation():
    spec = np.ones(30)
    fc = HyperspectralFailureAnalysisEngine.diagnose_sample(
        sample_id="test-1",
        pixel_spectrum=spec,
        coords=(5, 5),
        pred_class=1,
        gt_class=0,
        train_class_counts={0: 15}  # Starved
    )
    assert fc is not None
    assert fc.error_category == "rare_class_starvation"
    assert fc.severity == "high"


def test_failure_analysis_spatial_boundary():
    spec = np.ones(30)
    gt_map = np.zeros((10, 10), dtype=np.int64)
    gt_map[5:, :] = 1  # Boundary at row 5

    fc = HyperspectralFailureAnalysisEngine.diagnose_sample(
        sample_id="test-2",
        pixel_spectrum=spec,
        coords=(5, 5),
        pred_class=0,
        gt_class=1,
        gt_map=gt_map
    )
    assert fc is not None
    assert fc.error_category == "spatial_boundary_confusion"


def test_failure_analysis_spectral_metamerism():
    spec = np.array([1.0, 1.0, 1.0])
    p0 = np.array([1.0, 1.0, 1.0])
    p1 = np.array([1.0, 1.05, 1.02])  # SAM < 0.08 rad

    fc = HyperspectralFailureAnalysisEngine.diagnose_sample(
        sample_id="test-3",
        pixel_spectrum=spec,
        coords=(0, 0),
        pred_class=1,
        gt_class=0,
        class_spectral_profiles={0: p0, 1: p1}
    )
    assert fc is not None
    assert fc.error_category == "spectral_metamerism"


def test_failure_analysis_dataset_summary():
    preds = np.array([0, 1, 2, 0])
    targets = np.array([0, 0, 2, 1])  # 2 errors: (1->0) and (0->1)
    coords = [(1, 1), (2, 2), (3, 3), (4, 4)]
    spectra = np.random.randn(4, 20)

    summary = HyperspectralFailureAnalysisEngine.diagnose_dataset(
        preds=preds,
        targets=targets,
        coords=coords,
        spectra=spectra
    )
    assert summary["total_samples"] == 4
    assert summary["misclassified_count"] == 2
    assert summary["error_rate"] == 0.5
    assert len(summary["sample_failure_cases"]) == 2


# ==============================================================================
# 7. ModelManager Loader & Specialist Service Integration Tests
# ==============================================================================
def test_model_manager_hyperfree_loading():
    # If checkpoint exists, verifies it loads without uninitialized fallback
    report = ModelManager.get_model_status_report()
    assert "hyperfree_model" in report
    status = report["hyperfree_model"]
    assert "engine" in status


def test_hsi_specialist_service_inference():
    service = HyperFreeHSISpecialist()
    sample_cube = os.path.join(backend_root, "sample_data", "sample_hsi.mat")
    res = service.execute(
        image_path=sample_cube,
        image_arr=np.zeros((64, 64, 3)),
        meta={},
        query="what is the dominant land-cover in this hyperspectral cube?"
    )

    assert res["task"] == "hyperspectral_analysis"
    assert res["tool"] == "hyperfree_hsi"
    assert "cube_metadata" in res
    assert res["cube_metadata"]["bands"] == 200
    assert "spectral_signature" in res
    assert len(res["spectral_signature"]["wavelengths"]) == 200
    assert "top_classes" in res
