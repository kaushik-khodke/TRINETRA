"""
TRINETRA — Stage 1 Stabilization & Non-Deception Test Suite
Tests truthful checkpoint loading, transparent fallback observability,
deterministic tokenization, dynamic optical-SAR correlation, and malformed inputs.
"""

import os
import sys
import numpy as np
import pytest

# Ensure backend root is on sys.path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from models.loader import ModelManager
from models.tokenizer import deterministic_word_hash, tokenize_sequence
from geospatial.normalizer import GeospatialNormalizer
from services.captioning.captioning_service import RSCaptionSpecialist
from services.optical_sar.optical_sar_service import OpticalSarFusionSpecialist
from services.vqa.vqa_service import RSVqaSpecialist
from services.change.change_service import BiTemporalChangeSpecialist


class TestStage1ModelManagement:
    """Verifies honest status reporting and strict checkpoint loading."""

    def test_model_manager_truthful_status(self):
        status = ModelManager.get_status()
        assert isinstance(status, dict)
        assert "bigearthnet_adapted" in status
        assert "change_specialist_model" in status

        # bigearthnet_adapted currently has no weights file on disk
        bigearth = status["bigearthnet_adapted"]
        assert bigearth["loaded"] is False
        assert bigearth["fallback_active"] is True
        assert bigearth["checkpoint_file"] is None
        assert "Fallback" in bigearth["engine"]

        # Models with checkpoints on disk must report loaded: True with SHA256
        for key in ["change_specialist_model", "optical_sar_model", "rs_vqa_model"]:
            if status[key]["loaded"]:
                assert status[key]["checkpoint_hash"] is not None
                assert len(status[key]["checkpoint_hash"]) == 64
                assert status[key]["fallback_active"] is False

    def test_missing_checkpoint_refuses_random_weights(self):
        # Loading a model key with no weights file must return None, not an uninitialized network
        model = ModelManager.load_or_get_model("bigearthnet_adapted")
        assert model is None


class TestStage1DeterministicTokenizer:
    """Verifies that the tokenizer is 100% reproducible across process restarts."""

    def test_word_hash_determinism(self):
        # Must produce identical integer for identical words
        h1 = deterministic_word_hash("building", vocab_size=5000, offset=100)
        h2 = deterministic_word_hash("building", vocab_size=5000, offset=100)
        assert h1 == h2
        assert 100 <= h1 < 5000

        # Different words produce different hashes with high probability
        h_veg = deterministic_word_hash("vegetation", vocab_size=5000, offset=100)
        assert h1 != h_veg

        # Case-insensitive
        assert deterministic_word_hash("WATER") == deterministic_word_hash("water")

    def test_sequence_tokenization_structure(self):
        seq = "Is there significant water in this scene?"
        tokens = tokenize_sequence(seq, max_length=16, vocab_size=5000, offset=100)
        assert len(tokens) == 16
        # First 7 tokens must be non-zero word hashes for the 7 words
        assert all(t >= 100 for t in tokens[:7])
        # Remaining tokens must be PAD (0)
        assert all(t == 0 for t in tokens[7:])


class TestStage1DynamicOpticalSarCorrelation:
    """Verifies that optical-SAR correlation is computed dynamically and not hardcoded."""

    def test_dynamic_correlation_calculation(self):
        np.random.seed(42)
        base = np.random.rand(100, 100).astype(np.float32)

        # 1. Perfectly correlated inputs
        res_perf = GeospatialNormalizer.compute_cross_modal_correlation(base, base)
        assert pytest.approx(res_perf["optical_sar_correlation"], abs=0.01) == 1.0
        assert "High" in res_perf["structural_coherence"]

        # 2. Inverted inputs
        res_inv = GeospatialNormalizer.compute_cross_modal_correlation(base, -base)
        assert pytest.approx(res_inv["optical_sar_correlation"], abs=0.01) == -1.0
        assert "High" in res_inv["structural_coherence"]

        # 3. Independent noise inputs
        noise = np.random.rand(100, 100).astype(np.float32)
        res_noise = GeospatialNormalizer.compute_cross_modal_correlation(base, noise)
        assert abs(res_noise["optical_sar_correlation"]) < 0.25
        assert res_noise["optical_sar_correlation"] != 0.84  # Never static 0.84

    def test_zero_variance_handled_gracefully(self):
        flat = np.ones((50, 50), dtype=np.float32)
        res = GeospatialNormalizer.compute_cross_modal_correlation(flat, flat)
        assert res["optical_sar_correlation"] == 0.0


class TestStage1FallbackObservability:
    """Verifies that every service declares its fallback state and provenance."""

    def test_caption_specialist_fallback(self):
        spec = RSCaptionSpecialist()
        dummy_img = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)
        meta = {"modality": "optical", "width": 128, "height": 128}
        
        result = spec.execute(dummy_img, meta, "Summarize land cover", {})
        assert result["task"] == "captioning"
        assert result["requested_model"] == "bigearthnet_adapted"
        # Since bigearthnet has no weights file:
        assert result["fallback_used"] is True
        assert "No bigearthnet_adapted checkpoint" in result["fallback_reason"]
        assert result["confidence_calibrated"] is False
        assert 0.0 <= result["confidence"] <= 1.0

    def test_optical_sar_fallback_and_coregistration(self):
        spec = OpticalSarFusionSpecialist()
        opt = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        sar = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        
        # Test mismatched CRS
        metas_unaligned = [
            {"modality": "optical", "crs": "EPSG:4326"},
            {"modality": "sar", "crs": "EPSG:32643"}
        ]
        res = spec.execute([opt, sar], metas_unaligned, "Analyze urban and water", {})
        assert res["coregistered"] is False
        assert "Differing CRS" in res["fusion_correlations"]["spectral_radar_alignment"]
        assert res["confidence_calibrated"] is False
        assert res["fusion_correlations"]["optical_sar_correlation"] != 0.84

        # Test matched CRS
        metas_aligned = [
            {"modality": "optical", "crs": "EPSG:4326"},
            {"modality": "sar", "crs": "EPSG:4326"}
        ]
        res_aligned = spec.execute([opt, sar], metas_aligned, "Analyze urban and water", {})
        assert res_aligned["coregistered"] is True
        assert "Verified geometric coregistration" in res_aligned["fusion_correlations"]["spectral_radar_alignment"]

    def test_change_specialist_provenance(self):
        spec = BiTemporalChangeSpecialist()
        t1 = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)
        t2 = np.random.randint(0, 255, (128, 128, 3), dtype=np.uint8)
        metas = [{"modality": "optical"}, {"modality": "optical"}]

        res = spec.execute([t1, t2], metas, "What changed between T1 and T2?", {})
        assert res["task"] == "change_analysis"
        assert res["requested_model"] == "change_specialist_model"
        assert isinstance(res["fallback_used"], bool)
        assert res["confidence_calibrated"] is False
        assert "change_statistics" in res
