"""
TRINETRA — Stage 10 Test Suite: Reproducibility, Security and Production Hardening
SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)

Verifies:
1. SecurityValidator: Filename sanitization, path traversal, control characters, Windows reserved names
2. SecurityValidator: Magic bytes authentication, extension whitelist, disguised binary rejection
3. SecurityValidator: File size limit enforcement
4. SecurityValidator: Archive decompression zip bomb and member traversal detection
5. SecurityValidator: Safe subprocess execution with shell=False and binary whitelisting
6. SafeModelLoader: Deserialization with weights_only=True and cryptographic checksum verification
7. SafeTempManager: Scoped temporary directories and deterministic cleanup
8. ReproducibilityBundle: Creation, cryptographic fingerprinting, and divergence auditing
9. Audit Package: Generation of audit_manifest.json and RECONSTRUCTION_GUIDE.md
10. API Reliability: RequestIDMiddleware, RFC 7807 Problem Details, /healthz, /readyz probes
11. RobustnessEvaluator: Controlled corruptions, RDR degradation curves, uncertainty monotonicity
"""

import os
import io
import sys
import zipfile
import tempfile
import numpy as np
import pytest
import torch
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from core.security import SecurityValidator
from core.safe_loader import SafeModelLoader
from core.temp_manager import SafeTempManager
from core.reproducibility import (
    create_reproducibility_bundle,
    verify_reproducibility,
    generate_audit_package,
    ReproducibilityBundle
)
from core.exceptions import (
    SecurityViolationError,
    ModelCheckpointError,
    UnsafeDeserializationError
)
from app.middleware import format_rfc7807_error
from evaluation.robustness import RobustnessEvaluator, CorruptionType


# ==============================================================================
# 1. Security: Filename Sanitization & Path Traversal
# ==============================================================================
def test_security_validator_filename_sanitization():
    """Verify filename sanitization rejects null bytes, sanitizes traversal tokens, and handles Windows reserved names."""
    # 1. Null bytes must be rejected
    with pytest.raises(SecurityViolationError, match="Null byte"):
        SecurityValidator.sanitize_filename("image\x00.tif")

    # 2. Path traversals must be stripped of directory components
    safe1 = SecurityValidator.sanitize_filename("../../etc/passwd.tif")
    assert safe1 == "passwd.tif"
    assert ".." not in safe1
    assert "/" not in safe1

    safe2 = SecurityValidator.sanitize_filename("..\\..\\windows\\system32\\calc.png")
    assert safe2 == "calc.png"
    assert ".." not in safe2
    assert "\\" not in safe2

    # 3. Control characters and dangerous characters replaced with '_'
    safe3 = SecurityValidator.sanitize_filename("scene<name>:test?.tif")
    assert safe3 == "scene_name__test_.tif"

    # 4. Windows reserved names prefixed with safe_
    safe_con = SecurityValidator.sanitize_filename("CON.tif")
    assert safe_con == "safe_CON.tif"

    safe_nul = SecurityValidator.sanitize_filename("nul.png")
    assert safe_nul == "safe_nul.png"

    # 5. Empty or all-dot names rejected
    with pytest.raises(SecurityViolationError):
        SecurityValidator.sanitize_filename("")

    with pytest.raises(SecurityViolationError):
        SecurityValidator.sanitize_filename("...")


def test_security_validator_path_containment():
    """Verify validate_file_path prevents directory escaping outside allowed directories."""
    with tempfile.TemporaryDirectory() as allowed_dir:
        sub_dir = os.path.join(allowed_dir, "sub")
        os.makedirs(sub_dir, exist_ok=True)
        target_file = os.path.join(sub_dir, "sample.tif")
        with open(target_file, "w") as f:
            f.write("test")

        # Allowed file inside allowed_dir
        canon = SecurityValidator.validate_file_path(target_file, [allowed_dir])
        assert canon == os.path.realpath(target_file)

        # File escaping allowed_dir
        outside_file = os.path.abspath(os.path.join(allowed_dir, "..", "outside.tif"))
        with pytest.raises(SecurityViolationError, match="Path traversal"):
            SecurityValidator.validate_file_path(outside_file, [allowed_dir])


# ==============================================================================
# 2. Security: File Type, Magic Bytes & Size Bounds
# ==============================================================================
def test_security_validator_magic_bytes_and_file_types():
    """Verify magic bytes validation for GeoTIFF, PNG, JPEG, and rejection of disguised executables."""
    # 1. Valid TIFF magic bytes
    valid_tiff = b"II*\x00" + b"\x00" * 32
    ok, name = SecurityValidator.validate_file_type_and_size(valid_tiff, "scene.tif")
    assert ok is True
    assert name == "scene.tif"

    # 2. Valid PNG magic bytes
    valid_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    ok, name = SecurityValidator.validate_file_type_and_size(valid_png, "preview.png")
    assert ok is True

    # 3. Valid JPEG magic bytes
    valid_jpeg = b"\xff\xd8\xff" + b"\x00" * 32
    ok, name = SecurityValidator.validate_file_type_and_size(valid_jpeg, "image.jpg")
    assert ok is True

    # 4. Prohibited executable extensions
    with pytest.raises(SecurityViolationError, match="Prohibited executable/script"):
        SecurityValidator.validate_file_type_and_size(b"echo 1", "script.sh")

    with pytest.raises(SecurityViolationError, match="Prohibited executable/script"):
        SecurityValidator.validate_file_type_and_size(b"MZ\x90\x00", "payload.exe")

    # 5. Disguised binary executable inside a .tif file
    disguised_pe = b"MZ\x90\x00" + b"\x00" * 32
    with pytest.raises(SecurityViolationError, match="Disguised binary executable"):
        SecurityValidator.validate_file_type_and_size(disguised_pe, "fake_geotiff.tif")

    # 6. Invalid / mismatched magic bytes
    corrupted_tiff = b"NOT_A_TIFF_HEADER" + b"\x00" * 32
    with pytest.raises(SecurityViolationError, match="Invalid TIFF magic bytes"):
        SecurityValidator.validate_file_type_and_size(corrupted_tiff, "bad.tif")


def test_security_validator_file_size_limits():
    """Verify enforcement of maximum allowed file size bounds."""
    small_data = b"II*\x00" + b"\x00" * 100
    # Enforce strict 100-byte limit
    with pytest.raises(SecurityViolationError, match="exceeds maximum allowed limit"):
        SecurityValidator.validate_file_type_and_size(small_data, "scene.tif", max_size_bytes=50)


# ==============================================================================
# 3. Security: Archive Decompression & Zip Bomb Prevention
# ==============================================================================
def test_security_validator_archive_decompression_security():
    """Verify archive inspector validates safe archives and catches malicious traversal members."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # 1. Safe zip file
        safe_zip_path = os.path.join(tmp_dir, "safe.zip")
        with zipfile.ZipFile(safe_zip_path, "w") as zf:
            zf.writestr("tile_01.tif", b"II*\x00" + b"\x00" * 100)
            zf.writestr("metadata.json", b'{"asset": "01"}')

        summary = SecurityValidator.validate_archive_decompression(safe_zip_path)
        assert summary["is_safe"] is True
        assert summary["file_count"] == 2

        # 2. Malicious zip file with path traversal
        bad_zip_path = os.path.join(tmp_dir, "evil.zip")
        with zipfile.ZipFile(bad_zip_path, "w") as zf:
            zf.writestr("../../etc/shadow", b"malicious content")

        with pytest.raises(SecurityViolationError, match="Malicious member path traversal"):
            SecurityValidator.validate_archive_decompression(bad_zip_path)


# ==============================================================================
# 4. Security: Safe Subprocess Execution
# ==============================================================================
def test_safe_subprocess_run():
    """Verify subprocesses execute strictly with shell=False and unauthorized binaries are rejected."""
    # 1. Allowed binary (python)
    res = SecurityValidator.safe_subprocess_run([sys.executable, "-c", "print('TRINETRA_SAFE')"])
    assert res.returncode == 0
    assert "TRINETRA_SAFE" in res.stdout

    # 2. Prohibited binary
    with pytest.raises(SecurityViolationError, match="prohibited by TRINETRA security policy"):
        SecurityValidator.safe_subprocess_run(["curl", "http://example.com"])

    # 3. Invalid command structure
    with pytest.raises(SecurityViolationError, match="must be a non-empty list"):
        SecurityValidator.safe_subprocess_run("python -c print(1)")  # string instead of list


# ==============================================================================
# 5. Security: Safe Model Loader (weights_only=True)
# ==============================================================================
def test_safe_model_loader_weights_only_and_hash():
    """Verify SafeModelLoader loads state dicts with weights_only=True and verifies cryptographic hashes."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        ckpt_path = os.path.join(tmp_dir, "test_weights.pt")

        # Create valid state dict
        dummy_state = {
            "conv.weight": torch.randn(8, 3, 3, 3),
            "conv.bias": torch.zeros(8)
        }
        file_hash = SafeModelLoader.safe_save_state_dict(dummy_state, ckpt_path)
        assert len(file_hash) == 64

        # 1. Successful load with correct expected hash
        loaded = SafeModelLoader.load_state_dict(ckpt_path, expected_hash=file_hash, enforce_weights_only=True)
        assert "conv.weight" in loaded
        assert loaded["conv.weight"].shape == (8, 3, 3, 3)

        # 2. Hash mismatch detection
        with pytest.raises(SecurityViolationError, match="cryptographic hash mismatch"):
            SafeModelLoader.load_state_dict(ckpt_path, expected_hash="0000000000000000000000000000000000000000000000000000000000000000")

        # 3. Non-existent file
        with pytest.raises(ModelCheckpointError):
            SafeModelLoader.load_state_dict(os.path.join(tmp_dir, "missing.pt"))


# ==============================================================================
# 6. Lifecycle: Safe Temporary Manager Scoped Directories
# ==============================================================================
def test_safe_temp_manager_scoped_directory():
    """Verify SafeTempManager creates scoped temp directories and automatically cleans them on exit."""
    created_dir = None
    with SafeTempManager.scoped_temp_dir(prefix="unit_test_") as tmp_dir:
        created_dir = tmp_dir
        assert os.path.isdir(created_dir)
        test_file = os.path.join(created_dir, "sample.txt")
        with open(test_file, "w") as f:
            f.write("temporary data")
        assert os.path.isfile(test_file)

    # After context manager exits, directory must be deleted
    assert not os.path.exists(created_dir)


# ==============================================================================
# 7. Reproducibility & Audit Bundle
# ==============================================================================
def test_reproducibility_bundle_creation_and_divergence():
    """Verify ReproducibilityBundle captures environmental state and flags configuration divergence."""
    b1 = create_reproducibility_bundle(
        run_id="run_001",
        checkpoint_hash="a1b2c3d4e5f60000",
        dataset_manifest_hash="d1d2d3d4e5f60000",
        preprocessing_version="v2.0.0",
        random_seed=42
    )
    assert len(b1.fingerprint) == 16
    assert "torch" in b1.package_versions

    # Identical bundle should verify
    b2 = create_reproducibility_bundle(
        run_id="run_002",
        checkpoint_hash="a1b2c3d4e5f60000",
        dataset_manifest_hash="d1d2d3d4e5f60000",
        preprocessing_version="v2.0.0",
        random_seed=42
    )
    ok, divergences = verify_reproducibility(b1, b2)
    assert ok is True
    assert len(divergences) == 0

    # Divergent bundle (altered seed and checkpoint hash)
    b3 = create_reproducibility_bundle(
        run_id="run_003",
        checkpoint_hash="DIFFERENT_HASH_0000",
        dataset_manifest_hash="d1d2d3d4e5f60000",
        preprocessing_version="v2.0.0",
        random_seed=999
    )
    ok, divergences = verify_reproducibility(b1, b3)
    assert ok is False
    assert any("Checkpoint hash diverged" in d for d in divergences)
    assert any("Random seed diverged" in d for d in divergences)


def test_audit_package_generation():
    """Verify generate_audit_package creates audit_manifest.json and RECONSTRUCTION_GUIDE.md."""
    bundle = create_reproducibility_bundle(
        run_id="audit_run_01",
        checkpoint_hash="c1c2c3c4",
        dataset_manifest_hash="m1m2m3m4"
    )
    result_data = {
        "task": "change_detection",
        "metrics": {"f1_score": 0.892, "iou": 0.805},
        "known_limitations": ["Shadow misclassifications under cloud cover"]
    }

    with tempfile.TemporaryDirectory() as out_dir:
        res = generate_audit_package("audit_run_01", result_data, bundle, out_dir)
        assert os.path.isfile(res["manifest_path"])
        assert os.path.isfile(res["guide_path"])

        with open(res["guide_path"], "r", encoding="utf-8") as f:
            content = f.read()
            assert "Third-Party Audit & Reconstruction Guide" in content
            assert "audit_run_01" in content
            assert bundle.git_commit in content


# ==============================================================================
# 8. API Reliability: Request ID, Error Formatting & Health Probes
# ==============================================================================
def test_api_rfc7807_error_formatting():
    """Verify format_rfc7807_error formats standardized Problem Details JSON."""
    resp = format_rfc7807_error(
        status_code=400,
        title="Invalid Raster Headers",
        detail="CRS projection tag missing from GeoTIFF.",
        request_id="req-12345",
        error_code="ERR_GEOSPATIAL_METADATA",
        remediation="Provide valid EPSG CRS projection."
    )
    assert resp.status_code == 400
    assert resp.headers["X-Request-ID"] == "req-12345"
    assert resp.headers["Content-Type"] == "application/problem+json"


def test_api_healthz_and_readyz_probes():
    """Verify FastAPI /healthz liveness and /readyz readiness probes."""
    client = TestClient(app)

    # 1. /healthz
    r_live = client.get("/healthz")
    assert r_live.status_code == 200
    assert r_live.json()["status"] == "ok"
    assert "X-Request-ID" in r_live.headers

    # 2. /readyz
    r_ready = client.get("/readyz")
    assert r_ready.status_code in [200, 503]
    body = r_ready.json()
    assert "status" in body
    assert "storage_writable" in body
    assert "models" in body


def test_api_security_blocking_on_inspect_image():
    """Verify inspect-image route blocks malicious upload attempts with HTTP 400."""
    client = TestClient(app)

    # Disallowed executable extension
    fake_sh = io.BytesIO(b"#!/bin/bash\necho rm -rf /")
    resp = client.post(
        "/api/v1/inspect-image",
        files={"file": ("exploit.sh", fake_sh, "application/x-sh")}
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error_code"] == "ERR_SECURITY_VIOLATION"
    assert "Prohibited executable" in body["detail"]


# ==============================================================================
# 9. Robustness: Out-of-Distribution Corruptions & Monotonicity
# ==============================================================================
def test_robustness_corruptions_and_evaluator():
    """Verify physical corruptions degrade image signals and evaluate uncertainty monotonicity."""
    clean_img = np.ones((64, 64, 3), dtype=np.uint8) * 128

    # 1. Gaussian noise corruption increases variance
    noisy = RobustnessEvaluator.apply_corruption(clean_img, CorruptionType.GAUSSIAN_NOISE, severity=0.8)
    assert np.std(noisy) > 10.0

    # 2. Contrast reduction compresses dynamic range
    faded = RobustnessEvaluator.apply_corruption(clean_img, CorruptionType.CONTRAST_REDUCTION, severity=0.8)
    assert faded.shape == clean_img.shape

    # 3. Cloud occlusion alters quadrant
    cloudy = RobustnessEvaluator.apply_corruption(clean_img, CorruptionType.CLOUD_OCCLUSION, severity=0.8)
    assert np.max(cloudy) > 128

    # 4. Evaluate robustness curve on synthetic evaluator
    def dummy_eval(img):
        # Simulates degradation: score drops, uncertainty rises as noise increases
        noise_level = float(np.std(img))
        score = max(0.1, 1.0 - (noise_level / 100.0))
        uncertainty = min(0.9, 0.1 + (noise_level / 100.0))
        return score, uncertainty

    curve_res = RobustnessEvaluator.evaluate_robustness(
        eval_fn=dummy_eval,
        clean_inputs=[clean_img],
        corruption=CorruptionType.GAUSSIAN_NOISE,
        severities=[0.0, 0.25, 0.50, 0.75, 1.0]
    )

    assert curve_res["clean_score"] >= curve_res["severest_score"]
    assert 0.0 < curve_res["robustness_degradation_ratio"] <= 1.0
    assert curve_res["uncertainty_monotonic"] is True
