"""
TRINETRA / SatQuery AI — Stage 7 Automated Test Suite: Remote-Sensing VQA and Evidence
File: backend/tests/test_stage7_vqa_evidence.py

Validates:
1. VqaTokenizer: Versioned (v2.0.0), deterministic cryptographic SHA-256 fallback mapping,
   padding/truncation, vocabulary loading, and model compatibility bounds validation.
2. Ten-Point EvidencePackage Traceability: Every VQA answer references:
   (1) Source image (asset ID, file path, SHA-256, dimensions, sensor)
   (2) Bands/features used
   (3) Spatial region (bounds, CRS, physical area m^2, GeoJSON)
   (4) Model output (top answer, candidates, probabilities)
   (5) Confidence & calibration (score, calibrated bool, entropy)
   (6) Derived metrics (NDVI, NDWI, NDBI, water %, vegetation %, built-up %)
   (7) Timestamp (UTC ISO)
   (8) Checkpoint provenance (model name, file, SHA-256, param count)
   (9) Preprocessing (radiometric scaling, normalizer, input shape)
   (10) Warnings (cloud cover, OOD, fallback flags)
   and granular EvidenceItem records (E01, E02, E03).
3. RSVqaFusionNetwork: Multimodal visual feature + text GRU fusion architecture.
4. RS-VQA Metrics & Answer Verification: Top-1, Top-5, Exact Match, 95% bootstrap CI,
   and category breakdowns (Presence, Count, Comparison, Area).
5. RSVqaSpecialist Service: End-to-end execution returning grounded answers and evidence.
Governed by Stage 7 Remote-Sensing VQA & Evidence Protocol. Zero synthetic data in metric reporting.
"""

import os
import sys
import json
import tempfile
import importlib.util
import numpy as np
import pytest
import torch

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
rsvqa_dir = os.path.join(backend_root, "training", "02_rsvqa")
for p in [backend_root, rsvqa_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)


def _load_module(module_name: str, file_path: str):
    full_path = os.path.join(backend_root, file_path)
    spec = importlib.util.spec_from_file_location(module_name, full_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# Stage 7 Module Loaders
rsvqa_eval_mod = _load_module("stage7_rsvqa_evaluate", "training/02_rsvqa/evaluate.py")
evaluate_vqa_benchmark = rsvqa_eval_mod.evaluate_vqa_benchmark

rsvqa_model_mod = _load_module("stage7_rsvqa_model", "training/02_rsvqa/model.py")
RSVqaFusionNetwork = rsvqa_model_mod.RSVqaFusionNetwork

from schemas.contracts import (
    EvidencePackage,
    EvidenceItem,
    CandidateAnswer,
    VQAAnswerVerification,
    BenchmarkRun
)
from core.exceptions import ModelCheckpointError
from models.tokenizer import VqaTokenizer, tokenize_sequence
from services.vqa.evidence_engine import VQAEvidenceEngine
from services.vqa.vqa_service import RSVqaSpecialist
from training.common.metrics import vqa_metrics, categorize_question


# ==============================================================================
# 1. Tokenizer Governance Tests
# ==============================================================================

def test_vqa_tokenizer_deterministic_sha256():
    """Verify VqaTokenizer produces deterministic token sequences across invocations."""
    tokenizer = VqaTokenizer()
    query = "Is there a large river or water reservoir in the northern sector?"

    tokens_run1 = tokenizer.encode(query, max_length=16)
    tokens_run2 = tokenizer.encode(query, max_length=16)

    assert tokens_run1 == tokens_run2, "Tokenization must be 100% deterministic across invocations."
    assert len(tokens_run1) == 16, f"Expected 16 tokens, got {len(tokens_run1)}"
    assert all(isinstance(t, int) for t in tokens_run1)

    # Pad tokens must be 0
    short_tokens = tokenizer.encode("water", max_length=8)
    assert len(short_tokens) == 8
    assert short_tokens[-1] == 0, "Padded tokens must be zero."

    # Backwards compatibility function
    compat_tokens = tokenize_sequence(query, max_length=16)
    assert compat_tokens == tokens_run1, "tokenize_sequence must match VqaTokenizer.encode"


def test_vqa_tokenizer_vocab_loading_and_compatibility():
    """Verify vocabulary loading, decoding, and model vocabulary size validation."""
    tokenizer = VqaTokenizer()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tf:
        mock_vocab = {
            "ans2idx": {"yes": 0, "no": 1, "river": 2, "forest": 3, "urban": 4},
            "idx2ans": {"0": "yes", "1": "no", "2": "river", "3": "forest", "4": "urban"},
            "word2idx": {"<pad>": 0, "<unk>": 1, "is": 2, "there": 3, "water": 4, "river": 5},
            "idx2word": {"0": "<pad>", "1": "<unk>", "2": "is", "3": "there", "4": "water", "5": "river"}
        }
        json.dump(mock_vocab, tf)
        temp_vocab_path = tf.name

    try:
        count = tokenizer.load_vocab(temp_vocab_path)
        assert count == 6
        assert tokenizer.get_vocab_size() == 6

        # Encode known words
        encoded = tokenizer.encode("is there river", max_length=4)
        assert encoded[0] == 2  # 'is'
        assert encoded[1] == 3  # 'there'
        assert encoded[2] == 5  # 'river'
        assert encoded[3] == 0  # pad

        # Model compatibility check
        tokenizer.validate_compatibility(model_vocab_size=100)  # Should pass
        with pytest.raises(ValueError):
            tokenizer.validate_compatibility(model_vocab_size=4)  # Should fail (vocab_size=6 > 4)
    finally:
        if os.path.exists(temp_vocab_path):
            os.remove(temp_vocab_path)


# ==============================================================================
# 2. Ten-Point EvidencePackage Traceability Tests
# ==============================================================================

def test_vqa_evidence_package_all_ten_dimensions():
    """Verify that VQAEvidenceEngine generates all 10 required evidence dimensions."""
    H, W = 128, 128
    # Synthetic 3-band raster simulating optical imagery
    np.random.seed(42)
    img_arr = np.random.randint(40, 220, size=(H, W, 3), dtype=np.uint8)

    spectral_metrics = {
        "water_body_pct": 12.4,
        "vegetation_cover_pct": 45.2,
        "built_up_density_pct": 18.1,
        "bare_soil_pct": 24.3,
        "mean_ndvi": 0.42,
        "mean_ndwi": 0.18,
        "mean_ndbi": -0.15,
        "is_geotiff": True
    }

    meta = {
        "file_path": "tests/data/sample_scene.tif",
        "asset_id": "RS_SCENE_2026_001",
        "sensor": "Sentinel-2 MSI",
        "modality": "optical",
        "crs": "EPSG:32643",
        "bounds": [72.8, 18.9, 73.0, 19.1],
        "pixel_size_meters": 10.0
    }

    candidates = [
        CandidateAnswer(answer="yes", confidence=0.88),
        CandidateAnswer(answer="no", confidence=0.12)
    ]

    pkg = VQAEvidenceEngine.construct_evidence_package(
        image_arr=img_arr,
        meta=meta,
        query="Is there significant open water present?",
        spectral_metrics=spectral_metrics,
        top_answer="yes",
        candidates=candidates,
        confidence=0.88,
        is_calibrated=False,
        checkpoint_path="models/checkpoints/rs_vqa_model/model.pt",
        model_name="rs_vqa_fusion_v2",
        param_count=1245000,
        normalizer_name="GeospatialNormalizer.compute_spectral_breakdown",
        input_shape=[128, 128, 3],
        warnings=["Low cloud haze detected in SW quadrant"]
    )

    # 1. Source Image Traceability
    assert pkg.source_image.asset_id == "RS_SCENE_2026_001"
    assert pkg.source_image.file_path == "tests/data/sample_scene.tif"
    assert len(pkg.source_image.sha256) == 64
    assert pkg.source_image.dimensions == [128, 128, 3]
    assert pkg.source_image.sensor == "Sentinel-2 MSI"

    # 2. Bands / Features Used
    assert "Red (Band 4)" in pkg.bands_used
    assert "Green (Band 3)" in pkg.bands_used
    assert "Blue (Band 2)" in pkg.bands_used

    # 3. Spatial Region
    assert pkg.spatial_region.crs == "EPSG:32643"
    assert pkg.spatial_region.bounds == [72.8, 18.9, 73.0, 19.1]
    assert pkg.spatial_region.physical_area_sq_m == (128 * 10.0) * (128 * 10.0)
    assert pkg.spatial_region.geojson_geometry["type"] == "Polygon"

    # 4. Model Output
    assert pkg.model_output.top_answer == "yes"
    assert len(pkg.model_output.candidate_answers) == 2
    assert pkg.model_output.probabilities["yes"] == 0.88

    # 5. Confidence & Calibration
    assert pkg.confidence_and_calibration.confidence_score == 0.88
    assert pkg.confidence_and_calibration.is_calibrated is False
    assert pkg.confidence_and_calibration.entropy >= 0.0

    # 6. Derived Biophysical Metrics
    assert pkg.derived_metrics.water_pct == 12.4
    assert pkg.derived_metrics.vegetation_pct == 45.2
    assert pkg.derived_metrics.built_up_pct == 18.1
    assert pkg.derived_metrics.mean_ndvi == 0.42
    assert pkg.derived_metrics.mean_ndwi == 0.18

    # 7. Timestamp
    assert "T" in pkg.timestamp_utc and "Z" in pkg.timestamp_utc

    # 8. Checkpoint Provenance
    assert pkg.checkpoint_provenance.model_name == "rs_vqa_fusion_v2"
    assert pkg.checkpoint_provenance.checkpoint_path == "models/checkpoints/rs_vqa_model/model.pt"
    assert pkg.checkpoint_provenance.param_count == 1245000

    # 9. Preprocessing
    assert pkg.preprocessing.radiometric_scaling == "standard_uint8_0_to_1"
    assert pkg.preprocessing.input_shape == [128, 128, 3]

    # 10. Warnings
    assert "Low cloud haze detected in SW quadrant" in pkg.warnings

    # Granular Evidence Items
    assert len(pkg.evidence_items) >= 3
    ids = [item.item_id for item in pkg.evidence_items]
    assert "E01_WATER" in ids
    assert "E02_VEGETATION" in ids
    assert "E03_BUILT_UP" in ids

    # Round-trip serialization
    dumped = pkg.model_dump()
    json_str = pkg.model_dump_json()
    reloaded = EvidencePackage.model_validate_json(json_str)
    assert reloaded.package_id == pkg.package_id
    assert reloaded.source_image.sha256 == pkg.source_image.sha256


# ==============================================================================
# 3. RSVqaFusionNetwork Architecture Tests
# ==============================================================================

def test_rsvqa_fusion_network_forward_and_shapes():
    """Verify RSVqaFusionNetwork forward pass with single and multi-batch inputs."""
    vocab_size = 500
    num_answers = 25
    model = RSVqaFusionNetwork(vocab_size=vocab_size, num_answers=num_answers, text_dim=64, img_dim=128)
    model.eval()

    # Test single-item batch (B=1)
    img_b1 = torch.randn(1, 3, 224, 224)
    tokens_b1 = torch.randint(0, vocab_size, (1, 16), dtype=torch.long)
    with torch.no_grad():
        out_b1 = model(img_b1, tokens_b1)
    assert out_b1.shape == (1, num_answers), f"Expected (1, {num_answers}), got {out_b1.shape}"
    assert not torch.isnan(out_b1).any()
    assert not torch.isinf(out_b1).any()

    # Test multi-item batch (B=4)
    img_b4 = torch.randn(4, 3, 224, 224)
    tokens_b4 = torch.randint(0, vocab_size, (4, 16), dtype=torch.long)
    with torch.no_grad():
        out_b4 = model(img_b4, tokens_b4)
    assert out_b4.shape == (4, num_answers), f"Expected (4, {num_answers}), got {out_b4.shape}"


# ==============================================================================
# 4. RS-VQA Benchmark Metrics & Answer Verification Tests
# ==============================================================================

def test_vqa_benchmark_metrics_and_categories():
    """Verify vqa_metrics calculation, exact match, bootstrap CIs, and category breakdowns."""
    # 20 samples, 5 answers
    logits = np.array([
        [10.0, 1.0, 0.0, 0.0, 0.0],  # Pred 0, Target 0 (Correct)
        [0.0, 10.0, 1.0, 0.0, 0.0],  # Pred 1, Target 1 (Correct)
        [0.0, 0.0, 10.0, 1.0, 0.0],  # Pred 2, Target 2 (Correct)
        [10.0, 0.0, 0.0, 0.0, 0.0],  # Pred 0, Target 1 (Incorrect, top5 includes 1)
        [0.0, 10.0, 0.0, 0.0, 0.0],  # Pred 1, Target 0 (Incorrect)
        [10.0, 1.0, 0.0, 0.0, 0.0],  # Pred 0, Target 0 (Correct)
        [0.0, 10.0, 1.0, 0.0, 0.0],  # Pred 1, Target 1 (Correct)
        [0.0, 0.0, 10.0, 1.0, 0.0],  # Pred 2, Target 2 (Correct)
        [0.0, 0.0, 0.0, 10.0, 1.0],  # Pred 3, Target 3 (Correct)
        [0.0, 0.0, 0.0, 0.0, 10.0],  # Pred 4, Target 4 (Correct)
    ])
    targets = np.array([0, 1, 2, 1, 0, 0, 1, 2, 3, 4])
    questions = [
        "Is there a river in this image?",             # Presence
        "Are there buildings nearby?",                # Presence
        "How many bridges are visible?",              # Count
        "How many storage tanks exist?",              # Count
        "Is there more vegetation than bare soil?",   # Comparison
        "Is there greater urban density here?",       # Comparison
        "What is the total area of the lake?",        # Area
        "What is the size of the runway?",            # Area
        "Is there open water present?",               # Presence
        "What is visible here?"                       # Other
    ]
    idx2ans = {0: "yes", 1: "no", 2: "3", 3: "5", 4: "1000m2"}

    metrics = vqa_metrics(
        logits=logits,
        targets=targets,
        questions=questions,
        idx2ans=idx2ans,
        compute_ci=True,
        n_bootstraps=200
    )

    # 8 out of 10 correct = 80.0%
    assert metrics["top1_accuracy_pct"] == 80.0
    assert metrics["exact_match_pct"] == 80.0
    assert metrics["top5_accuracy_pct"] == 100.0  # all targets within top 5
    assert metrics["num_samples"] == 10

    # Bootstrap CI
    ci = metrics["top1_ci_95"]
    assert len(ci) == 2
    assert ci[0] <= metrics["top1_accuracy_pct"] <= ci[1]

    # Category Breakdown
    cat = metrics["category_breakdown"]
    assert "presence" in cat
    assert "count" in cat
    assert "comparison" in cat
    assert "area" in cat
    assert cat["presence"]["count"] == 3
    assert cat["count"]["count"] == 2
    assert cat["comparison"]["count"] == 2
    assert cat["area"]["count"] == 2


def test_vqa_answer_verification_contract():
    """Verify VQAAnswerVerification contract fields and validation."""
    v = VQAAnswerVerification(
        question="Is there a river present?",
        predicted_answer="yes",
        ground_truth_answer="yes",
        is_correct=True,
        is_top5_correct=True,
        top5_candidates=["yes", "no", "river", "lake", "none"],
        question_category="presence"
    )
    assert v.is_correct is True
    assert v.question_category == "presence"
    d = v.model_dump()
    assert d["predicted_answer"] == "yes"
    assert len(d["top5_candidates"]) == 5


# ==============================================================================
# 5. RSVqaSpecialist Service End-to-End Execution Tests
# ==============================================================================

def test_rsvqa_specialist_service_execution():
    """Verify RSVqaSpecialist executes cleanly, generating answers and 10-point evidence packages."""
    specialist = RSVqaSpecialist()
    assert specialist.tool_id == "rs_vqa"

    # Create realistic test raster
    np.random.seed(123)
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:, :50, 1] = 180  # Green vegetation on left half
    img[:, 50:, 0] = 160  # Reddish soil on right half

    meta = {
        "file_path": "memory://test_scene.png",
        "asset_id": "TEST_VQA_001",
        "modality": "optical",
        "sensor": "Synthetic Test Sensor"
    }

    query = "Is there green vegetation present in this satellite observation?"
    params = {"response_language": "en"}

    result = specialist.execute(img, meta, query, params)

    # Response schema validation
    assert result["task"] == "vqa"
    assert result["tool"] == "rs_vqa"
    assert result["query"] == query
    assert isinstance(result["answer"], str) and len(result["answer"]) > 10
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["fallback_used"] in [True, False]
    assert "evidence_package" in result
    assert "evidence_items" in result
    assert "evidence_image" in result
    assert "raw_preview" in result

    # Validate embedded EvidencePackage conforms to contract
    pkg_dict = result["evidence_package"]
    pkg = EvidencePackage.model_validate(pkg_dict)
    assert pkg.source_image.dimensions == [100, 100, 3]
    assert pkg.derived_metrics.vegetation_pct >= 0.0
    assert len(pkg.evidence_items) >= 3

    # Check evidence items
    item_ids = [it["item_id"] for it in result["evidence_items"]]
    assert "E01_WATER" in item_ids
    assert "E02_VEGETATION" in item_ids
    assert "E03_BUILT_UP" in item_ids
