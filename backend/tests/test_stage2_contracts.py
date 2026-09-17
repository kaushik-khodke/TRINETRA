"""
TRINETRA — Stage 2 Architecture Contracts & Configuration Test Suite
Tests settings integrity, provenance fingerprinting, and all 12 Pydantic schemas.
"""

import os
import sys
import pytest
from pydantic import ValidationError

# Ensure backend root is on sys.path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from config.settings import settings
from core.provenance import (
    compute_data_sha256,
    generate_run_fingerprint,
    create_provenance_record,
    get_environment_lock_hash
)
from core.exceptions import (
    TRINETRABaseException,
    InputValidationError,
    GeospatialValidationError,
    ModelCheckpointError
)
from schemas.contracts import (
    InputAsset,
    RasterMetadata,
    AlignmentReport,
    TaskRequest,
    ModelRun,
    QuantumModelRun,
    Prediction,
    MetricSet,
    EvidenceItem,
    ProvenanceRecord,
    ValidationResult,
    BenchmarkRun,
    FailureCase
)
from models.loader import ModelManager


class TestStage2Settings:
    """Verifies centralized configuration and zero magic numbers."""

    def test_settings_initialization(self):
        assert settings.app_name == "TRINETRA"
        assert settings.app_version == "2.2.0"
        assert settings.seed == 42
        assert os.path.isdir(settings.checkpoints_dir)
        assert os.path.isdir(settings.uploads_dir)

    def test_config_hash_determinism(self):
        h1 = settings.get_config_hash()
        h2 = settings.get_config_hash()
        assert len(h1) == 64
        assert h1 == h2


class TestStage2ProvenanceAndFingerprint:
    """Verifies deterministic run fingerprinting and provenance manifests."""

    def test_run_fingerprint_determinism(self):
        git_commit = "abcd1234efgh5678"
        cfg_hash = settings.get_config_hash()
        inputs = ["hash1", "hash2"]
        ckpts = ["ckpt_hash_a"]

        fp1 = generate_run_fingerprint(git_commit, cfg_hash, inputs, ckpts)
        fp2 = generate_run_fingerprint(git_commit, cfg_hash, inputs, ckpts)
        assert len(fp1) == 16
        assert fp1 == fp2

        # Change in inputs must alter fingerprint
        fp3 = generate_run_fingerprint(git_commit, cfg_hash, ["different_hash"], ckpts)
        assert fp1 != fp3

    def test_provenance_record_generation(self):
        prov_dict = create_provenance_record(
            run_id="run-001",
            input_hashes=["a" * 64],
            checkpoint_hashes=["b" * 64],
            fallback_active=False
        )
        record = ProvenanceRecord(**prov_dict)
        assert record.run_id == "run-001"
        assert len(record.run_fingerprint) == 16
        assert record.schema_version == "2.0.0"
        assert record.random_seed == 42


class TestStage2PydanticContracts:
    """Tests validation and constraints across all Stage 2 contracts."""

    def test_input_asset_valid_and_invalid(self):
        valid = InputAsset(
            asset_id="asset-1",
            filename="sentinel2_t1.tif",
            file_path="/tmp/sentinel2_t1.tif",
            file_size_bytes=1024,
            sha256_hash="a" * 64,
            mime_type="image/tiff",
            created_at="2026-09-16T00:00:00Z"
        )
        assert valid.asset_id == "asset-1"

        # Invalid: sha256_hash length != 64
        with pytest.raises(ValidationError):
            InputAsset(
                asset_id="asset-2",
                filename="test.tif",
                file_path="/tmp/test.tif",
                file_size_bytes=100,
                sha256_hash="invalid_short_hash",
                created_at="2026-09-16T00:00:00Z"
            )

    def test_raster_metadata_validation(self):
        meta = RasterMetadata(
            width=512,
            height=512,
            band_count=4,
            dtype="uint16",
            crs="EPSG:32643",
            bounds=[100.0, 200.0, 150.0, 250.0],
            resolution=[10.0, 10.0],
            sensor_name="Sentinel-2B",
            modality="multispectral"
        )
        assert meta.width == 512
        assert meta.modality == "multispectral"

        # Negative width must fail
        with pytest.raises(ValidationError):
            RasterMetadata(width=-5, height=512, band_count=3)

    def test_alignment_report(self):
        report = AlignmentReport(
            source_crs="EPSG:4326",
            reference_crs="EPSG:4326",
            bounds_overlap_pct=98.5,
            grid_aligned=True,
            resolution_ratio=1.0,
            coregistered=True,
            status_message="Full sub-pixel coregistration verified"
        )
        assert report.coregistered is True
        assert report.bounds_overlap_pct == 98.5

    def test_model_run_and_quantum_model_run(self):
        # Test ModelManager helper produces valid ModelRun
        run_data = ModelManager.build_model_run_record(
            model_key="change_specialist_model",
            run_id="run-123",
            latency_ms=45.2,
            fallback_used=False
        )
        m_run = ModelRun(**run_data)
        assert m_run.run_id == "run-123"
        assert m_run.requested_model == "change_specialist_model"
        assert m_run.schema_version == "2.0.0"

        # Test QuantumModelRun extension
        q_run = QuantumModelRun(
            run_id="q-run-001",
            requested_model="qml_change_vqc",
            engine_type="PennyLane Quantum VQC",
            device="cpu",
            latency_ms=88.0,
            qubit_count=6,
            circuit_depth=3,
            simulator_backend="default.qubit",
            classical_baseline_agreement=0.85
        )
        assert q_run.qubit_count == 6
        assert q_run.classical_baseline_agreement == 0.85

    def test_metric_set_rejects_simulated_metrics(self):
        # Valid real metric
        metric = MetricSet(
            primary_metric_name="Overall Accuracy",
            primary_metric_value=0.885,
            quantitative_metrics={"F1": 0.87, "IoU": 0.78},
            is_simulated=False,
            provenance_note="Measured against LEVIR-CD official test split"
        )
        assert metric.primary_metric_value == 0.885

        # Strict rule: is_simulated=True must raise ValidationError
        with pytest.raises(ValidationError):
            MetricSet(
                primary_metric_name="Simulated Accuracy",
                primary_metric_value=0.99,
                is_simulated=True
            )

    def test_evidence_item_and_failure_case(self):
        ev = EvidenceItem(
            evidence_id="E01",
            evidence_type="differential",
            title="Bi-temporal Change Hotspot",
            description="Normalized spectral difference exceeding 0.22 threshold",
            source_layer="B4-B8 Delta",
            numeric_value=38.4,
            unit="%"
        )
        assert ev.evidence_type == "differential"

        fc = FailureCase(
            case_id="FC-001",
            actual_output={"class": "Unchanged"},
            error_category="cloud_shadow",
            severity="medium",
            explanation="Dense cumulus cloud shadow in T2 suppressed NIR reflectance",
            mitigation="Engage SAR microwave backscatter specialist to bypass cloud cover"
        )
        assert fc.error_category == "cloud_shadow"
        assert fc.severity == "medium"


class TestStage2Exceptions:
    """Verifies domain exception hierarchy and serialization."""

    def test_exception_serialization(self):
        exc = GeospatialValidationError(
            message="Raster header lacks valid projection",
            context={"file": "sample.tif"}
        )
        d = exc.to_dict()
        assert d["error_code"] == "ERR_GEOSPATIAL_METADATA"
        assert d["severity"] == "high"
        assert d["context"]["file"] == "sample.tif"
        assert "projection" in d["mitigation"]
