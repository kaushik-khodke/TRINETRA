"""
TRINETRA — Stage 4 Bi-Temporal Change Detection Unit & Integration Tests
Validates:
1. SiameseUNetBaseline & BitemporalInteractionTransformer architecture mechanics.
2. HybridBCEDiceLoss numerical properties.
3. binary_change_mask_metrics (pixel & object-level stats).
4. ChangeDatasetValidator (pairing, dimensions, and split leakage detection).
5. ChangeFailureAnalysisEngine (diagnostic taxonomy into FailureCase records).
6. Change specialist end-to-end integration.
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

training_dir = os.path.join(backend_root, "training", "04_change")
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

from models.change_models import (
    SiameseUNetBaseline,
    BitemporalInteractionTransformer,
    create_change_model
)
from training.common.metrics import binary_change_mask_metrics
import importlib.util

def _load_module(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod

change_model_mod = _load_module("training_04_change_model", os.path.join(training_dir, "model.py"))
HybridBCEDiceLoss = change_model_mod.HybridBCEDiceLoss
DiceLoss = change_model_mod.DiceLoss

change_val_mod = _load_module("training_04_change_validate", os.path.join(training_dir, "validate_dataset.py"))
ChangeDatasetValidator = change_val_mod.ChangeDatasetValidator

change_fail_mod = _load_module("training_04_change_failure", os.path.join(training_dir, "failure_analysis.py"))
ChangeFailureAnalysisEngine = change_fail_mod.ChangeFailureAnalysisEngine

from schemas.contracts import FailureCase
from core.exceptions import DatasetValidationError, DatasetLeakageError
from services.change.change_service import BiTemporalChangeSpecialist




# ==============================================================================
# 1. Architecture Mechanics Tests
# ==============================================================================
class TestChangeArchitectures:
    """Validates baseline and transformer model dimensions, params, and gradients."""

    def test_siamese_unet_baseline_forward_backward(self):
        model = SiameseUNetBaseline(in_channels=3, num_classes=1, base_channels=16)
        t1 = torch.randn(2, 3, 128, 128, requires_grad=True)
        t2 = torch.randn(2, 3, 128, 128, requires_grad=True)

        logits = model(t1, t2)
        assert logits.shape == (2, 1, 128, 128), f"Expected (2, 1, 128, 128), got {logits.shape}"

        loss = logits.sum()
        loss.backward()
        assert t1.grad is not None and t2.grad is not None

        # Verify parameter count within laptop budget (< 5M)
        param_count = sum(p.numel() for p in model.parameters())
        assert param_count < 5_000_000, f"Baseline param count {param_count} exceeds budget"

    def test_bit_transformer_forward_backward(self):
        model = BitemporalInteractionTransformer(in_channels=3, num_classes=1, token_len=4, embed_dim=64, num_layers=2)
        t1 = torch.randn(2, 3, 128, 128, requires_grad=True)
        t2 = torch.randn(2, 3, 128, 128, requires_grad=True)

        logits = model(t1, t2)
        assert logits.shape == (2, 1, 128, 128), f"Expected (2, 1, 128, 128), got {logits.shape}"

        loss = logits.sum()
        loss.backward()
        assert t1.grad is not None and t2.grad is not None

        # Verify parameter count within laptop budget (< 5M)
        param_count = sum(p.numel() for p in model.parameters())
        assert param_count < 5_000_000, f"BIT param count {param_count} exceeds budget"

    def test_change_model_factory(self):
        baseline = create_change_model("baseline")
        assert isinstance(baseline, SiameseUNetBaseline)

        bit = create_change_model("bit")
        assert isinstance(bit, BitemporalInteractionTransformer)

        with pytest.raises(ValueError, match="Unknown change detection architecture"):
            create_change_model("nonexistent_arch")



# ==============================================================================
# 2. Loss Function Tests
# ==============================================================================
class TestHybridLoss:
    """Validates Dice and Hybrid BCE+Dice losses."""

    def test_dice_loss_bounds(self):
        loss_fn = DiceLoss()
        # Near-identical prediction
        logits = torch.ones(1, 1, 32, 32) * 10.0
        targets = torch.ones(1, 1, 32, 32)
        loss_near_zero = loss_fn(logits, targets).item()
        assert loss_near_zero < 0.05

        # Inverted prediction
        logits_inv = torch.ones(1, 1, 32, 32) * -10.0
        loss_high = loss_fn(logits_inv, targets).item()
        assert loss_high > 0.90

    def test_hybrid_bce_dice_loss(self):
        criterion = HybridBCEDiceLoss(bce_weight=0.5, dice_weight=0.5)
        logits = torch.randn(2, 1, 64, 64, requires_grad=True)
        targets = torch.randint(0, 2, (2, 1, 64, 64)).float()

        loss = criterion(logits, targets)
        assert loss.item() > 0.0
        loss.backward()
        assert logits.grad is not None


# ==============================================================================
# 3. Dense Metrics Tests
# ==============================================================================
class TestDenseChangeMetrics:
    """Validates pixel-level and object-level change metrics."""

    def test_perfect_prediction_metrics(self):
        gt = np.zeros((100, 100), dtype=np.uint8)
        gt[20:40, 20:40] = 1
        gt[60:80, 60:80] = 1

        pred = gt.copy().astype(float)
        m = binary_change_mask_metrics(pred, gt)

        assert m["f1"] == 1.0
        assert m["iou"] == 1.0
        assert m["precision"] == 1.0
        assert m["recall"] == 1.0
        assert m["accuracy"] == 1.0
        assert m["confusion_matrix"]["tp"] == 800
        assert m["confusion_matrix"]["fp"] == 0
        assert m["confusion_matrix"]["fn"] == 0
        assert m["object_metrics"]["gt_object_count"] == 2
        assert m["object_metrics"]["detected_objects"] == 2
        assert m["object_metrics"]["false_alarm_objects"] == 0

    def test_complete_miss_metrics(self):
        gt = np.zeros((100, 100), dtype=np.uint8)
        gt[20:40, 20:40] = 1
        pred = np.zeros((100, 100), dtype=float)

        m = binary_change_mask_metrics(pred, gt)
        assert m["recall"] == 0.0
        assert m["f1"] == 0.0
        assert m["iou"] == 0.0
        assert m["confusion_matrix"]["fn"] == 400
        assert m["object_metrics"]["missed_objects"] == 1

    def test_shape_mismatch_raises(self):
        pred = np.zeros((50, 50))
        gt = np.zeros((60, 60))
        with pytest.raises(ValueError, match="Shape mismatch"):
            binary_change_mask_metrics(pred, gt)


# ==============================================================================
# 4. Dataset Validation & Leakage Prevention Tests
# ==============================================================================
class TestDatasetValidator:
    """Tests raster pairing, dimension check, and split leakage detection."""

    @pytest.fixture
    def temp_dataset_dir(self):
        tmp = tempfile.mkdtemp(prefix="trinetra_cd_test_")
        for split in ["train", "val", "test"]:
            s_dir = os.path.join(tmp, split)
            os.makedirs(os.path.join(s_dir, "A"))
            os.makedirs(os.path.join(s_dir, "B"))
            os.makedirs(os.path.join(s_dir, "label"))

            # Create sample files
            for i in range(3):
                sid = f"{split}_sample_{i}"
                img = Image.new("RGB", (64, 64), color=(100 + i*10, 100, 100))
                lbl = Image.new("L", (64, 64), color=0)
                img.save(os.path.join(s_dir, "A", f"{sid}.png"))
                img.save(os.path.join(s_dir, "B", f"{sid}.png"))
                lbl.save(os.path.join(s_dir, "label", f"{sid}.png"))

        yield tmp
        shutil.rmtree(tmp, ignore_errors=True)

    def test_valid_manifest_build(self, temp_dataset_dir):
        manifest = ChangeDatasetValidator.build_dataset_manifest(temp_dataset_dir)
        assert manifest["summary"]["total_verified_pairs"] == 9
        assert manifest["leakage_audit"]["leakage_free"] is True

    def test_dimension_mismatch_rejection(self, temp_dataset_dir):
        # Corrupt one image to have different dimensions
        bad_img = Image.new("RGB", (128, 128))
        bad_path = os.path.join(temp_dataset_dir, "train", "B", "train_sample_0.png")
        bad_img.save(bad_path)

        triplets = ChangeDatasetValidator.discover_split_samples(os.path.join(temp_dataset_dir, "train"))
        with pytest.raises(DatasetValidationError, match="Dimension mismatch"):
            ChangeDatasetValidator.validate_split_integrity(triplets, "train")

    def test_data_leakage_detection(self):
        train_ids = {"pair_1", "pair_2", "pair_3"}
        val_ids = {"pair_4", "pair_5"}
        test_ids = {"pair_3", "pair_6"}  # pair_3 leaked into test!

        with pytest.raises(DatasetLeakageError, match="Data leakage detected.*TRAIN and TEST"):
            ChangeDatasetValidator.verify_split_leakage(train_ids, val_ids, test_ids)


# ==============================================================================
# 5. Failure Analysis Engine Tests
# ==============================================================================
class TestFailureAnalysisEngine:
    """Validates automated autopsy of failure cases into FailureCase contracts."""

    def test_small_object_miss_diagnosis(self):
        t1 = np.ones((3, 100, 100), dtype=np.float32) * 0.5
        t2 = np.ones((3, 100, 100), dtype=np.float32) * 0.5
        gt = np.zeros((100, 100), dtype=np.uint8)
        # Small 3x3 object (area = 9 px < 40)
        gt[10:13, 10:13] = 1
        pred = np.zeros((100, 100), dtype=float)

        fail = ChangeFailureAnalysisEngine.diagnose_sample("sample_01", t1, t2, pred, gt)
        assert fail is not None
        assert isinstance(fail, FailureCase)
        assert fail.error_category == "small_object_miss"
        assert "small changed objects" in fail.explanation

    def test_boundary_error_diagnosis(self):
        t1 = np.ones((3, 100, 100), dtype=np.float32) * 0.5
        t2 = np.ones((3, 100, 100), dtype=np.float32) * 0.5
        gt = np.zeros((100, 100), dtype=np.uint8)
        gt[30:70, 30:70] = 1
        # Prediction slightly dilated by 1 pixel along perimeter
        pred = np.zeros((100, 100), dtype=float)
        pred[29:71, 29:71] = 1.0

        fail = ChangeFailureAnalysisEngine.diagnose_sample("sample_02", t1, t2, pred, gt, iou_threshold=0.95)
        assert fail is not None
        assert fail.error_category == "boundary_error"

    def test_cloud_shadow_false_alarm_diagnosis(self):
        t1 = np.ones((3, 100, 100), dtype=np.float32) * 0.8
        t2 = np.ones((3, 100, 100), dtype=np.float32) * 0.8
        # Add dark cast shadow in T2
        t2[:, 40:60, 40:60] = 0.05
        gt = np.zeros((100, 100), dtype=np.uint8)  # No genuine change
        pred = np.zeros((100, 100), dtype=float)
        pred[40:60, 40:60] = 1.0  # Falsely triggered by shadow

        fail = ChangeFailureAnalysisEngine.diagnose_sample("sample_03", t1, t2, pred, gt)
        assert fail is not None
        assert fail.error_category == "cloud_shadow"
        assert "shadow" in fail.actual_output.lower()

    def test_failure_report_generation(self):
        fc1 = FailureCase(
            case_id="f1", actual_output="fp", error_category="false_positive",
            explanation="fp err", severity="medium", mitigation="Hard negative mining"
        )
        fc2 = FailureCase(
            case_id="f2", actual_output="shadow", error_category="cloud_shadow",
            explanation="shadow err", severity="high", mitigation="Color invariant norm"
        )
        report = ChangeFailureAnalysisEngine.generate_failure_report([fc1, fc2])
        assert report["total_failures"] == 2
        assert "cloud_shadow" in report["breakdown"]
        assert "false_positive" in report["breakdown"]
        assert len(report["recommended_mitigations"]) == 2


# ==============================================================================
# 6. Specialist Integration Test
# ==============================================================================
class TestChangeSpecialistIntegration:
    """Tests BiTemporalChangeSpecialist execution end-to-end."""

    def test_specialist_execution(self):
        specialist = BiTemporalChangeSpecialist()
        t1 = np.ones((128, 128, 3), dtype=np.uint8) * 100
        t2 = np.ones((128, 128, 3), dtype=np.uint8) * 100
        # Add simulated structure to t2
        t2[30:60, 30:60] = 220

        meta1 = {
            "width": 128,
            "height": 128,
            "crs": "EPSG:4326",
            "bounds": [77.0, 28.0, 77.1, 28.1],
            "modality": "optical"
        }
        meta2 = {
            "width": 128,
            "height": 128,
            "crs": "EPSG:4326",
            "bounds": [77.0, 28.0, 77.1, 28.1],
            "modality": "optical"
        }

        result = specialist.execute(
            images_arr=[t1, t2],
            metas=[meta1, meta2],
            query="Detect structural change between observations",
            parameters={"response_language": "en"}
        )

        assert "answer" in result
        assert "change_statistics" in result
        assert "evidence" in result
        assert "change_heatmap" in result["evidence"]
        stats = result["change_statistics"]
        assert "changed_area_percentage" in stats
        assert float(stats["changed_area_percentage"]) > 0.0


