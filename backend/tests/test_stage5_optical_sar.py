"""
TRINETRA — Stage 5 Optical + SAR Multimodal Unit & Integration Tests
Validates:
1. OpticalSARConcatBaseline, OpticalSARGatedFusionNet, OpticalSARCrossAttentionNet architectures.
2. Single-sensor ablations (OpticalOnlyBaseline, SAROnlyBaseline).
3. Factory adapter (create_optical_sar_model).
4. Fusion gain calculations (fusion_metrics).
5. OpticalSARDatasetValidator (pairing, dimensions, and split leakage detection).
6. OpticalSARFailureAnalysisEngine (multimodal diagnostic taxonomy into FailureCase records).
7. OpticalSarFusionSpecialist end-to-end integration.
Zero synthetic or mock data in benchmarks.
"""

import os
import sys
import tempfile
import shutil
import pytest
import numpy as np
import torch
from PIL import Image

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

training_dir = os.path.join(backend_root, "training", "05_optical_sar")
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from models.optical_sar_models import (
    OpticalSARConcatBaseline,
    OpticalSARGatedFusionNet,
    OpticalSARCrossAttentionNet,
    OpticalOnlyBaseline,
    SAROnlyBaseline,
    create_optical_sar_model
)
from training.common.metrics import fusion_metrics
import importlib.util

def _load_module(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

optsar_val_mod = _load_module("training_05_optsar_validate", os.path.join(training_dir, "validate_dataset.py"))
OpticalSARDatasetValidator = optsar_val_mod.OpticalSARDatasetValidator

optsar_fail_mod = _load_module("training_05_optsar_failure", os.path.join(training_dir, "failure_analysis.py"))
OpticalSARFailureAnalysisEngine = optsar_fail_mod.OpticalSARFailureAnalysisEngine

from schemas.contracts import FailureCase
from core.exceptions import DatasetValidationError, DatasetLeakageError
from services.optical_sar.optical_sar_service import OpticalSarFusionSpecialist


# ==============================================================================
# 1. Architecture Mechanics Tests
# ==============================================================================
class TestOpticalSARArchitectures:
    """Validates dimensions, parameter counts, and gradient flows for all fusion models."""

    def test_concat_baseline_forward_backward(self):
        model = OpticalSARConcatBaseline(opt_channels=3, sar_channels=2, embed_dim=32, num_classes=10)
        opt = torch.randn(2, 3, 64, 64, requires_grad=True)
        sar = torch.randn(2, 2, 64, 64, requires_grad=True)

        logits = model(opt, sar)
        assert logits.shape == (2, 10), f"Expected (2, 10), got {logits.shape}"

        loss = logits.sum()
        loss.backward()
        assert opt.grad is not None and sar.grad is not None

        param_count = sum(p.numel() for p in model.parameters())
        assert param_count < 2_000_000, f"Concat param count {param_count} exceeds budget"

    def test_gated_fusion_forward_backward(self):
        model = OpticalSARGatedFusionNet(opt_channels=3, sar_channels=2, embed_dim=32, num_classes=10)
        opt = torch.randn(2, 3, 64, 64, requires_grad=True)
        sar = torch.randn(2, 2, 64, 64, requires_grad=True)

        logits = model(opt, sar)
        assert logits.shape == (2, 10), f"Expected (2, 10), got {logits.shape}"

        loss = logits.sum()
        loss.backward()
        assert opt.grad is not None and sar.grad is not None

        param_count = sum(p.numel() for p in model.parameters())
        assert param_count < 2_000_000, f"Gated param count {param_count} exceeds budget"

    def test_cross_attention_forward_backward(self):
        model = OpticalSARCrossAttentionNet(opt_channels=3, sar_channels=2, embed_dim=32, num_heads=2, num_classes=10)
        opt = torch.randn(2, 3, 64, 64, requires_grad=True)
        sar = torch.randn(2, 2, 64, 64, requires_grad=True)

        logits = model(opt, sar)
        assert logits.shape == (2, 10), f"Expected (2, 10), got {logits.shape}"

        loss = logits.sum()
        loss.backward()
        assert opt.grad is not None and sar.grad is not None

        param_count = sum(p.numel() for p in model.parameters())
        assert param_count < 2_000_000, f"Cross-attention param count {param_count} exceeds budget"

    def test_single_modality_ablations(self):
        opt_model = OpticalOnlyBaseline(opt_channels=3, embed_dim=32, num_classes=10)
        sar_model = SAROnlyBaseline(sar_channels=2, embed_dim=32, num_classes=10)

        opt = torch.randn(2, 3, 64, 64)
        sar = torch.randn(2, 2, 64, 64)

        out_opt = opt_model(opt)
        out_sar = sar_model(sar)

        assert out_opt.shape == (2, 10)
        assert out_sar.shape == (2, 10)

    def test_create_optical_sar_model_factory(self):
        m_concat = create_optical_sar_model("concat")
        assert isinstance(m_concat, OpticalSARConcatBaseline)

        m_gated = create_optical_sar_model("gated")
        assert isinstance(m_gated, OpticalSARGatedFusionNet)

        m_attn = create_optical_sar_model("cross_attention")
        assert isinstance(m_attn, OpticalSARCrossAttentionNet)

        m_opt = create_optical_sar_model("optical_only")
        assert isinstance(m_opt, OpticalOnlyBaseline)

        m_sar = create_optical_sar_model("sar_only")
        assert isinstance(m_sar, SAROnlyBaseline)

        with pytest.raises(ValueError, match="Unknown Optical-SAR architecture"):
            create_optical_sar_model("invalid_model")


# ==============================================================================
# 2. Fusion Gain Metrics Tests
# ==============================================================================
class TestFusionMetrics:
    """Validates multimodal comparative gain computations."""

    def test_fusion_metrics_positive_gain(self):
        opt_acc = 78.5
        sar_acc = 72.0
        fused_acc = 84.0

        m = fusion_metrics(opt_acc, sar_acc, fused_acc)
        assert m["optical_only_accuracy"] == 78.5
        assert m["sar_only_accuracy"] == 72.0
        assert m["optical_sar_fused_accuracy"] == 84.0
        assert m["fusion_delta_vs_optical"] == 5.5
        assert m["fusion_delta_vs_sar"] == 12.0
        assert m["fusion_outperforms_both"] is True

    def test_fusion_metrics_negative_gain(self):
        opt_acc = 85.0
        sar_acc = 70.0
        fused_acc = 82.0

        m = fusion_metrics(opt_acc, sar_acc, fused_acc)
        assert m["fusion_delta_vs_optical"] == -3.0
        assert m["fusion_outperforms_both"] is False


# ==============================================================================
# 3. Dataset Validation & Leakage Detection Tests
# ==============================================================================
class TestOpticalSARDatasetValidator:
    """Tests raster pairing, dimension check, and split leakage detection."""

    @pytest.fixture
    def temp_dataset_dir(self):
        tmp = tempfile.mkdtemp(prefix="trinetra_optsar_test_")
        s1_dir = os.path.join(tmp, "s1")
        s2_dir = os.path.join(tmp, "s2")
        os.makedirs(s1_dir)
        os.makedirs(s2_dir)

        # Create 5 matched pairs
        for i in range(5):
            sid = f"patch_{i:03d}"
            opt_img = Image.new("RGB", (64, 64), color=(120, 100 + i*10, 80))
            sar_img = Image.new("L", (64, 64), color=50 + i*20)

            opt_img.save(os.path.join(s2_dir, f"{sid}.png"))
            sar_img.save(os.path.join(s1_dir, f"{sid}.png"))

        yield tmp
        shutil.rmtree(tmp, ignore_errors=True)

    def test_valid_manifest_build(self, temp_dataset_dir):
        manifest = OpticalSARDatasetValidator.build_dataset_manifest(temp_dataset_dir)
        assert manifest["summary"]["total_verified_pairs"] == 5
        assert manifest["metrics"]["inspected_pairs"] == 5

    def test_dimension_mismatch_rejection(self, temp_dataset_dir):
        # Corrupt one SAR image dimension
        bad_sar = Image.new("L", (128, 128))
        bad_sar.save(os.path.join(temp_dataset_dir, "s1", "patch_000.png"))

        pairs = OpticalSARDatasetValidator.discover_pairs(temp_dataset_dir)
        with pytest.raises(DatasetValidationError, match="Dimension mismatch"):
            OpticalSARDatasetValidator.validate_split_integrity(pairs, "all")

    def test_data_leakage_detection(self):
        train_ids = {"patch_1", "patch_2", "patch_3"}
        val_ids = {"patch_4", "patch_5"}
        test_ids = {"patch_2", "patch_6"}  # patch_2 leaked into test

        with pytest.raises(DatasetLeakageError, match="Data leakage detected.*TRAIN and TEST"):
            OpticalSARDatasetValidator.verify_split_leakage(train_ids, val_ids, test_ids)


# ==============================================================================
# 4. Multimodal Failure Analysis Engine Tests
# ==============================================================================
class TestOpticalSARFailureAnalysis:
    """Validates automated autopsy of multimodal prediction errors."""

    def test_cloud_occlusion_diagnosis(self):
        # Heavily saturated optical (cloud)
        opt = np.ones((3, 64, 64), dtype=np.float32) * 0.95
        sar = np.ones((2, 64, 64), dtype=np.float32) * 0.30

        fail = OpticalSARFailureAnalysisEngine.diagnose_sample(
            sample_id="patch_cloud_01",
            opt_arr=opt,
            sar_arr=sar,
            pred_class=8,  # Barren Soil (misclassified)
            gt_class=3     # Forest Canopy
        )

        assert fail is not None
        assert isinstance(fail, FailureCase)
        assert fail.error_category == "cloud_shadow"
        assert "cloud cover" in fail.explanation

    def test_sar_saturation_diagnosis(self):
        opt = np.ones((3, 64, 64), dtype=np.float32) * 0.40
        # Heavily saturated radar return
        sar = np.ones((2, 64, 64), dtype=np.float32) * 0.99

        fail = OpticalSARFailureAnalysisEngine.diagnose_sample(
            sample_id="patch_sat_01",
            opt_arr=opt,
            sar_arr=sar,
            pred_class=0,
            gt_class=6
        )

        assert fail is not None
        assert fail.error_category == "sensor_saturation"
        assert "radar backscatter saturation" in fail.explanation

    def test_model_divergence_diagnosis(self):
        opt = np.ones((3, 64, 64), dtype=np.float32) * 0.50
        sar = np.ones((2, 64, 64), dtype=np.float32) * 0.50

        fail = OpticalSARFailureAnalysisEngine.diagnose_sample(
            sample_id="patch_div_01",
            opt_arr=opt,
            sar_arr=sar,
            pred_class=2,  # Agriculture
            gt_class=0,    # Urban
            opt_only_class=0,  # Opt said Urban
            sar_only_class=6   # SAR said Water
        )

        assert fail is not None
        assert fail.error_category == "model_divergence"
        assert "diverged sharply" in fail.explanation

    def test_failure_report_generation(self):
        fc1 = FailureCase(
            case_id="f1", actual_output="cloud", error_category="cloud_shadow",
            explanation="cloud occlusion", severity="high", mitigation="Increase SAR weight"
        )
        fc2 = FailureCase(
            case_id="f2", actual_output="div", error_category="model_divergence",
            explanation="encoder divergence", severity="medium", mitigation="Cross-modal alignment"
        )
        report = OpticalSARFailureAnalysisEngine.generate_failure_report([fc1, fc2])
        assert report["total_failures"] == 2
        assert "cloud_shadow" in report["breakdown"]
        assert "model_divergence" in report["breakdown"]


# ==============================================================================
# 5. Specialist Integration Test
# ==============================================================================
class TestOpticalSarSpecialistIntegration:
    """Tests OpticalSarFusionSpecialist execution end-to-end."""

    def test_specialist_execution(self):
        specialist = OpticalSarFusionSpecialist()

        opt = np.ones((128, 128, 3), dtype=np.uint8) * 120
        # Add high optical green band
        opt[:, :, 1] = 210

        sar = np.ones((128, 128), dtype=np.uint8) * 40

        meta_opt = {
            "width": 128,
            "height": 128,
            "crs": "EPSG:4326",
            "bounds": [77.0, 28.0, 77.1, 28.1],
            "modality": "optical"
        }
        meta_sar = {
            "width": 128,
            "height": 128,
            "crs": "EPSG:4326",
            "bounds": [77.0, 28.0, 77.1, 28.1],
            "modality": "sar"
        }

        result = specialist.execute(
            images_arr=[opt, sar],
            metas=[meta_opt, meta_sar],
            query="Analyze cross-modal optical and SAR signatures",
            parameters={"response_language": "en"}
        )

        assert "answer" in result
        assert "alignment_report" in result
        assert "fusion_correlations" in result
        assert "optical_sar_correlation" in result["fusion_correlations"]
        assert "sensor_contributions" in result
        assert "evidence" in result
        assert "fused_composite" in result["evidence"]

