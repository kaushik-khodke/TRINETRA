"""
TRINETRA — Typed Architecture Contracts & Domain Schemas
SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)

Implements Stage 2 Pydantic schemas across all service boundaries:
Input -> Ingest -> Metadata -> Alignment -> ModelRun -> Prediction -> Evidence -> Provenance.
Enforces zero magic numbers, strict type hints, and immutable contract versioning.
"""

from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, Field, field_validator


# ==============================================================================
# 1. Ingest & Input Boundary
# ==============================================================================
class InputAsset(BaseModel):
    """Represents a validated input raster, array, or geospatial file."""
    schema_version: str = Field(default="2.0.0", description="Contract release version")
    asset_id: str = Field(..., description="Unique asset UUID")
    filename: str = Field(..., description="Original client filename")
    file_path: str = Field(..., description="Verified local absolute file path")
    file_size_bytes: int = Field(..., ge=0, description="Exact file size in bytes")
    sha256_hash: str = Field(..., min_length=64, max_length=64, description="Cryptographic SHA-256 digest")
    mime_type: str = Field(default="image/tiff", description="Detected media MIME type")
    created_at: str = Field(..., description="ISO 8601 UTC creation timestamp")


class RasterMetadata(BaseModel):
    """Geospatial raster metadata extracted directly from file headers (GDAL/Rasterio/TIFF)."""
    schema_version: str = Field(default="2.0.0")
    width: int = Field(..., gt=0, description="Raster width in pixels")
    height: int = Field(..., gt=0, description="Raster height in pixels")
    band_count: int = Field(..., gt=0, description="Number of spectral/polarimetric channels")
    dtype: str = Field(default="float32", description="Data type representation")
    nodata_value: Optional[float] = Field(default=None, description="Explicit nodata mask value")
    crs: Optional[str] = Field(default=None, description="Coordinate reference system (e.g. EPSG:4326)")
    transform_matrix: Optional[List[float]] = Field(default=None, description="6-element affine geotransform")
    bounds: Optional[List[float]] = Field(default=None, description="[minx, miny, maxx, maxy] bounding box")
    resolution: Optional[List[float]] = Field(default=None, description="[pixel_width, pixel_height] in CRS units")
    sensor_name: str = Field(default="Generic / Unknown Sensor", description="Platform identifier")
    modality: Literal["optical", "sar", "hyperspectral", "multispectral"] = Field(
        default="optical", description="Resolved physical sensor modality"
    )
    is_geotiff: bool = Field(default=False, description="True if georeferencing metadata present")
    acquisition_timestamp: Optional[str] = Field(default=None, description="ISO 8601 acquisition timestamp if present")
    band_descriptions: Optional[List[str]] = Field(default=None, description="Names/channels of spectral bands")
    filename: Optional[str] = Field(default="", description="Original raster filename")
    center_lat: Optional[float] = Field(default=None, description="Center latitude in degrees")
    center_lng: Optional[float] = Field(default=None, description="Center longitude in degrees")
    location_name: Optional[str] = Field(default=None, description="Geographic location identifier")

    @property
    def has_geographic_location(self) -> bool:
        return self.center_lat is not None and self.center_lng is not None

    def to_dict(self) -> Dict[str, Any]:
        """Backwards compatibility helper for existing service call-sites."""
        d = self.model_dump()
        d["bands"] = self.band_count
        d["has_geographic_location"] = self.has_geographic_location
        return d

    @field_validator("bounds")
    @classmethod
    def validate_bounds_length(cls, v):
        if v is not None and len(v) != 4:
            raise ValueError("Bounds must contain exactly 4 coordinates: [minx, miny, maxx, maxy]")
        return v


# ==============================================================================
# 2. Geospatial Alignment Boundary
# ==============================================================================
class AlignmentReport(BaseModel):
    """Geometric verification report produced before bi-temporal or multimodal execution."""
    schema_version: str = Field(default="2.0.0")
    source_crs: Optional[str] = Field(default=None, description="Source raster coordinate system")
    reference_crs: Optional[str] = Field(default=None, description="Target/reference raster coordinate system")
    bounds_overlap_pct: float = Field(..., ge=0.0, le=100.0, description="Calculated spatial bounding intersection")
    grid_aligned: bool = Field(..., description="True if pixel origins and grid resolutions match exactly")
    resolution_ratio: float = Field(default=1.0, gt=0.0, description="Pixel resolution ratio (source / reference)")
    reprojection_needed: bool = Field(default=False, description="True if CRS transformation is required")
    resampling_applied: bool = Field(default=False, description="True if on-the-fly resampling was performed")
    resampling_method: Optional[str] = Field(default=None, description="Resampling kernel: bilinear | nearest")
    coregistered: bool = Field(..., description="True only if geometric verification passes strict tolerance")
    offset_vector: Optional[List[float]] = Field(default=None, description="[dx, dy] estimated spatial registration shift")
    intersection_bounds: Optional[List[float]] = Field(default=None, description="[minx, miny, maxx, maxy] overlap bbox")
    valid_data_overlap_pct: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Overlap excluding nodata")
    temporal_order_valid: Optional[bool] = Field(default=None, description="True if t1 <= t2 in bi-temporal analysis")
    status_message: str = Field(..., description="Human-readable geometric audit summary")


# ==============================================================================
# 3. Task & Request Boundary
# ==============================================================================
class TaskRequest(BaseModel):
    """Structured operational task request processed by the orchestrator."""
    schema_version: str = Field(default="2.0.0")
    request_id: str = Field(..., description="Unique client query execution UUID")
    query: str = Field(..., min_length=1, description="Natural language question or command")
    resolved_task: Literal["change_analysis", "optical_sar_fusion", "vqa", "grounding", "captioning", "hyperspectral_analysis"] = Field(
        ..., description="Resolved domain specialist task"
    )
    input_assets: List[InputAsset] = Field(default_factory=list, description="Validated raster input assets")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Execution overrides and thresholds")
    response_language: str = Field(default="en", description="ISO 639-1 language tag: en | hi | mr")
    timestamp_utc: str = Field(..., description="ISO 8601 UTC submission timestamp")


# ==============================================================================
# 4. Model Execution & Inference Boundary
# ==============================================================================
class ModelRun(BaseModel):
    """Machine-readable record of an individual neural forward pass or fallback execution."""
    schema_version: str = Field(default="2.0.0")
    run_id: str = Field(..., description="Unique model inference run UUID")
    requested_model: str = Field(..., description="Target neural architecture identifier")
    loaded_model: Optional[str] = Field(default=None, description="Actual model filename if neural checkpoint loaded")
    checkpoint_path: Optional[str] = Field(default=None, description="Local path to weights file")
    checkpoint_hash: Optional[str] = Field(default=None, description="SHA-256 hash of loaded checkpoint")
    engine_type: str = Field(..., description="Detailed description of execution engine")
    device: str = Field(default="cpu", description="Execution hardware device: cuda | cpu | mps")
    parameter_count: Optional[int] = Field(default=None, description="Trainable parameter count")
    latency_ms: float = Field(..., ge=0.0, description="Execution wall-clock time in milliseconds")
    fallback_used: bool = Field(default=False, description="True if heuristic/algorithmic fallback ran")
    fallback_reason: Optional[str] = Field(default=None, description="Reason why fallback was engaged")


class QuantumModelRun(ModelRun):
    """Extended ModelRun contract for the PennyLane QML experimental research branch."""
    qubit_count: int = Field(default=6, ge=1, le=32, description="Quantum wire count")
    circuit_depth: int = Field(default=3, ge=1, description="Parameterized variational ansatz layer depth")
    simulator_backend: str = Field(default="default.qubit", description="PennyLane simulator device target")
    shots: Optional[int] = Field(default=None, description="Measurement sample shots (None for analytic statevector)")
    classical_baseline_agreement: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Agreement ratio against matched classical baseline"
    )


class Prediction(BaseModel):
    """Standardized prediction payload across all remote-sensing specialists."""
    schema_version: str = Field(default="2.0.0")
    task: str = Field(..., description="Executed specialist task")
    detected_classes: List[str] = Field(default_factory=list, description="Top predicted class labels")
    class_probabilities: Dict[str, float] = Field(default_factory=dict, description="Softmax confidence distribution")
    bounding_boxes: List[Dict[str, Any]] = Field(default_factory=list, description="Detected object bounding boxes")
    segmentation_mask_present: bool = Field(default=False, description="True if 2D segmentation array was computed")
    change_status: Optional[str] = Field(default=None, description="Bi-temporal trend classification")
    raw_metrics: Dict[str, Any] = Field(default_factory=dict, description="Low-level radiometric or sensor statistics")


# ==============================================================================
# 5. Scientific Metrics & Evidence Boundary
# ==============================================================================
class MetricSet(BaseModel):
    """Scientifically auditable metrics produced from real raster math."""
    schema_version: str = Field(default="2.0.0")
    primary_metric_name: str = Field(..., description="Canonical metric: e.g. Overall Accuracy, F1, IoU, Pearson r")
    primary_metric_value: float = Field(..., description="Calculated scalar value")
    quantitative_metrics: Dict[str, Any] = Field(default_factory=dict, description="Full dictionary of computed metrics")
    is_simulated: bool = Field(default=False, description="Must be False for real remote-sensing evaluations")
    provenance_note: Optional[str] = Field(default=None, description="Data source and protocol attribution")

    @field_validator("is_simulated")
    @classmethod
    def reject_simulated_metrics(cls, v):
        if v is True:
            raise ValueError("Zero synthetic/simulated metrics rule: is_simulated must be False for scientific audit.")
        return v


class EvidenceItem(BaseModel):
    """Machine-readable evidence object grounding an analytical conclusion."""
    schema_version: str = Field(default="2.0.0")
    evidence_id: str = Field(..., description="Unique evidence token (e.g. E01)")
    evidence_type: Literal["spectral", "spatial", "radar", "differential", "multimodal"] = Field(
        ..., description="Domain classification of evidence"
    )
    title: str = Field(..., description="Concise evidence heading")
    description: str = Field(..., description="Physical explanation of what was measured")
    source_layer: str = Field(..., description="Band or raster channel used for measurement")
    numeric_value: Optional[float] = Field(default=None, description="Extracted numerical scalar")
    unit: Optional[str] = Field(default=None, description="Engineering unit: % | dB | index | m^2")
    overlay_base64: Optional[str] = Field(default=None, description="Base64 encoded visual overlay or heatmap")
    geojson_geometry: Optional[Dict[str, Any]] = Field(default=None, description="GeoJSON polygon or feature collection")


# ==============================================================================
# 6. Auditability & Provenance Boundary
# ==============================================================================
class ProvenanceRecord(BaseModel):
    """End-to-end cryptographic and environment provenance manifest."""
    schema_version: str = Field(default="2.0.0")
    run_id: str = Field(..., description="Unique execution run UUID")
    run_fingerprint: str = Field(..., min_length=16, max_length=16, description="16-char deterministic execution fingerprint")
    timestamp_utc: str = Field(..., description="ISO 8601 UTC execution timestamp")
    git_commit: str = Field(..., description="Git commit hash of running code")
    environment_lock_hash: str = Field(..., description="Hash of pinned scientific package versions")
    config_hash: str = Field(..., description="SHA-256 hash of active system configuration")
    dataset_manifest_hash: Optional[str] = Field(default=None, description="Checksum of reference dataset if benchmarked")
    input_hashes: List[str] = Field(default_factory=list, description="SHA-256 digests of all input rasters")
    checkpoint_hashes: List[str] = Field(default_factory=list, description="SHA-256 digests of all engaged model weights")
    random_seed: int = Field(default=42, description="Active pseudo-random seed")
    device_name: str = Field(default="cuda", description="Computing device utilized")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings recorded during execution")
    fallback_active: bool = Field(default=False, description="True if any model was substituted with heuristic fallback")


class ValidationResult(BaseModel):
    """Integrity check result evaluating files, schemas, or dataset splits."""
    schema_version: str = Field(default="2.0.0")
    is_valid: bool = Field(..., description="True if all critical checks passed")
    errors: List[str] = Field(default_factory=list, description="Fatal validation error descriptions")
    warnings: List[str] = Field(default_factory=list, description="Advisory or non-blocking issues")
    checks_executed: List[str] = Field(default_factory=list, description="List of validated assertions")


# ==============================================================================
# 7. Benchmarking & Debugging Boundary
# ==============================================================================
class BenchmarkRun(BaseModel):
    """Standardized result manifest from an official dataset evaluation run."""
    schema_version: str = Field(default="2.0.0")
    benchmark_id: str = Field(..., description="Unique benchmark run UUID")
    dataset_name: str = Field(..., description="Canonical benchmark dataset: e.g. LEVIR-CD, SEN12MS, Indian Pines")
    dataset_manifest_hash: str = Field(..., description="Integrity hash of verified dataset directory")
    split: Literal["train", "val", "test"] = Field(..., description="Dataset split evaluated (test run only for final gate)")
    sample_count: int = Field(..., gt=0, description="Total verified sample pairs/cubes evaluated")
    metrics: Dict[str, float] = Field(..., description="Standard published metrics: Acc, F1, IoU, Precision, Recall")
    confidence_interval_95: Optional[Dict[str, List[float]]] = Field(
        default=None, description="Bootstrap 95% confidence intervals [lower, upper] per metric"
    )
    hardware_profile: Dict[str, Any] = Field(default_factory=dict, description="CPU/GPU hardware specs")
    execution_time_seconds: float = Field(..., ge=0.0, description="Total benchmark evaluation duration")


class FailureCase(BaseModel):
    """Structured failure diagnosis recorded during validation or benchmarking."""
    schema_version: str = Field(default="2.0.0")
    case_id: str = Field(..., description="Unique failure case identifier")
    asset_id: Optional[str] = Field(default=None, description="Target asset identifier")
    expected_output: Optional[Any] = Field(default=None, description="Ground truth reference value if known")
    actual_output: Any = Field(..., description="Erroneous prediction or output produced")
    error_category: Literal[
        "misregistration",
        "cloud_shadow",
        "out_of_distribution",
        "model_divergence",
        "sensor_saturation",
        "missing_modality",
        "other"
    ] = Field(..., description="Root-cause classification of failure")
    severity: Literal["low", "medium", "high", "critical"] = Field(default="medium")
    explanation: str = Field(..., description="Technical autopsy explaining why failure occurred")
    mitigation: Optional[str] = Field(default=None, description="Proposed algorithmic or data fix")
