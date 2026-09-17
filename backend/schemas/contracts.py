"""
TRINETRA — Typed Architecture Contracts & Domain Schemas
SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)

Implements Stage 2 Pydantic schemas across all service boundaries:
Input -> Ingest -> Metadata -> Alignment -> ModelRun -> Prediction -> Evidence -> Provenance.
Enforces zero magic numbers, strict type hints, and immutable contract versioning.
"""

import uuid
from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict


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
    evidence_id: str = Field(default="", description="Unique evidence token (e.g. E01)")
    item_id: str = Field(default="", description="Alias for evidence_id (e.g. E01_WATER)")
    evidence_type: Literal["spectral", "spatial", "radar", "differential", "multimodal"] = Field(
        default="spectral", description="Domain classification of evidence"
    )
    title: str = Field(..., description="Concise evidence heading")
    description: str = Field(..., description="Physical explanation of what was measured")
    source_layer: str = Field(..., description="Band or raster channel used for measurement")
    numeric_value: Optional[float] = Field(default=None, description="Extracted numerical scalar")
    unit: Optional[str] = Field(default=None, description="Engineering unit: % | dB | index | m^2")
    overlay_base64: Optional[str] = Field(default=None, description="Base64 encoded visual overlay or heatmap")
    geojson_geometry: Optional[Dict[str, Any]] = Field(default=None, description="GeoJSON polygon or feature collection")
    model_config = ConfigDict(extra="allow")

    def __init__(self, **data):
        if "item_id" in data and not data.get("evidence_id"):
            data["evidence_id"] = data["item_id"]
        elif "evidence_id" in data and not data.get("item_id"):
            data["item_id"] = data["evidence_id"]
        super().__init__(**data)


class CandidateAnswer(BaseModel):
    """Ranked candidate answer predicted by visual question answering."""
    schema_version: str = Field(default="2.0.0")
    answer: str = Field(..., description="Predicted answer string or class")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    rank: int = Field(default=1, ge=1, description="Ranking position (1 = top-1)")
    model_config = ConfigDict(extra="allow")


class VQAAnswerVerification(BaseModel):
    """Auditable comparison of predicted VQA answer against benchmark ground truth."""
    schema_version: str = Field(default="2.0.0")
    question_id: str = Field(default_factory=lambda: f"q-{uuid.uuid4().hex[:8]}", description="Unique question identifier")
    question: str = Field(default="", description="Natural language question text")
    query: str = Field(default="", description="Alias for question")
    ground_truth_answer: str = Field(..., description="Verified benchmark reference answer")
    predicted_answer: str = Field(..., description="Model top-1 predicted answer")
    candidate_answers: List[CandidateAnswer] = Field(default_factory=list, description="Top-k ranked candidates")
    top5_candidates: List[str] = Field(default_factory=list, description="Top-5 candidate answer strings")
    exact_match: bool = Field(default=False, description="True if predicted_answer matches ground_truth_answer")
    is_correct: bool = Field(default=False, description="Alias for exact_match")
    top5_match: bool = Field(default=False, description="True if ground truth is within top-5 candidates")
    is_top5_correct: bool = Field(default=False, description="Alias for top5_match")
    question_category: Optional[str] = Field(default=None, description="Category: presence | count | comparison | area | other")
    model_config = ConfigDict(extra="allow")

    def __init__(self, **data):
        if "question" in data and not data.get("query"):
            data["query"] = data["question"]
        elif "query" in data and not data.get("question"):
            data["question"] = data["query"]
        if "is_correct" in data and "exact_match" not in data:
            data["exact_match"] = data["is_correct"]
        elif "exact_match" in data and "is_correct" not in data:
            data["is_correct"] = data["exact_match"]
        if "is_top5_correct" in data and "top5_match" not in data:
            data["top5_match"] = data["is_top5_correct"]
        elif "top5_match" in data and "is_top5_correct" not in data:
            data["is_top5_correct"] = data["top5_match"]
        super().__init__(**data)


# ------------------------------------------------------------------------------
# Ten-Point Traceability Sub-Models
# ------------------------------------------------------------------------------
class SourceImageTraceability(BaseModel):
    asset_id: str = Field(default="unknown_asset")
    file_path: str = Field(default="memory://raster")
    sha256: str = Field(default="")
    sha256_hash: str = Field(default="")
    dimensions: List[int] = Field(default_factory=list)
    sensor: str = Field(default="Remote Sensing Platform")
    modality: str = Field(default="optical")
    model_config = ConfigDict(extra="allow")

    def __init__(self, **data):
        if "sha256_hash" in data and not data.get("sha256"):
            data["sha256"] = data["sha256_hash"]
        elif "sha256" in data and not data.get("sha256_hash"):
            data["sha256_hash"] = data["sha256"]
        super().__init__(**data)


class SpatialRegionTraceability(BaseModel):
    crs: str = Field(default="EPSG:4326")
    bounds: List[float] = Field(default_factory=list)
    physical_area_sq_m: Optional[float] = None
    physical_area_m2: Optional[float] = None
    geojson_geometry: Dict[str, Any] = Field(default_factory=dict)
    geojson: Dict[str, Any] = Field(default_factory=dict)
    pixel_dimensions: Optional[List[int]] = None
    model_config = ConfigDict(extra="allow")

    def __init__(self, **data):
        if "physical_area_m2" in data and not data.get("physical_area_sq_m"):
            data["physical_area_sq_m"] = data["physical_area_m2"]
        elif "physical_area_sq_m" in data and not data.get("physical_area_m2"):
            data["physical_area_m2"] = data["physical_area_sq_m"]
        if "geojson" in data and not data.get("geojson_geometry"):
            data["geojson_geometry"] = data["geojson"]
        elif "geojson_geometry" in data and not data.get("geojson"):
            data["geojson"] = data["geojson_geometry"]
        super().__init__(**data)


class ModelOutputTraceability(BaseModel):
    top_answer: Optional[str] = None
    candidate_answers: List[CandidateAnswer] = Field(default_factory=list)
    candidates: List[Dict[str, Any]] = Field(default_factory=list)
    probabilities: Dict[str, float] = Field(default_factory=dict)
    neural_evaluated: bool = False
    model_config = ConfigDict(extra="allow")


class ConfidenceCalibrationTraceability(BaseModel):
    confidence_score: float = 0.85
    score: float = 0.85
    is_calibrated: bool = False
    confidence_calibrated: bool = False
    entropy: float = 0.0
    margin_to_second: Optional[float] = None
    brier_score: Optional[float] = None
    expected_calibration_error: Optional[float] = None
    max_calibration_error: Optional[float] = None
    temperature_applied: Optional[float] = None
    confidence_semantics: Optional[str] = "probability_class_correctness"
    aleatoric_uncertainty: Optional[float] = None
    epistemic_uncertainty: Optional[float] = None
    data_quality_uncertainty: Optional[float] = None
    registration_uncertainty: Optional[float] = None
    model_config = ConfigDict(extra="allow")

    def __init__(self, **data):
        if "score" in data and "confidence_score" not in data:
            data["confidence_score"] = data["score"]
        elif "confidence_score" in data and "score" not in data:
            data["score"] = data["confidence_score"]
        if "confidence_calibrated" in data and "is_calibrated" not in data:
            data["is_calibrated"] = data["confidence_calibrated"]
        elif "is_calibrated" in data and "confidence_calibrated" not in data:
            data["confidence_calibrated"] = data["is_calibrated"]
        super().__init__(**data)


class ReliabilityDiagramData(BaseModel):
    """Binned reliability diagram statistics for confidence calibration curves."""
    bin_edges: List[float] = Field(..., description="Edges of confidence intervals [0, 1]")
    bin_accuracies: List[float] = Field(..., description="Observed empirical accuracy per bin")
    bin_confidences: List[float] = Field(..., description="Mean predicted confidence per bin")
    bin_counts: List[int] = Field(..., description="Sample count per bin")
    ece: float = Field(..., description="Expected Calibration Error")
    mce: float = Field(..., description="Maximum Calibration Error")
    brier_score: float = Field(..., description="Brier calibration score")
    model_config = ConfigDict(extra="allow")


class UncertaintyReport(BaseModel):
    """Decomposed multi-source uncertainty quantification report."""
    confidence_semantics: str = Field(..., description="Quantified semantic: e.g. probability_class_correctness")
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Calibrated top prediction confidence")
    aleatoric_uncertainty: float = Field(..., ge=0.0, le=1.0, description="Data ambiguity / normalized Shannon entropy")
    epistemic_uncertainty: float = Field(..., ge=0.0, le=1.0, description="Model uncertainty / OOD distance")
    data_quality_uncertainty: float = Field(..., ge=0.0, le=1.0, description="Sensor noise, cloud, shadow, or saturation")
    registration_uncertainty: float = Field(..., ge=0.0, le=1.0, description="Coregistration offset or spatial disparity")
    quality_flags: List[str] = Field(default_factory=list, description="Explicit data quality warning tags")
    model_config = ConfigDict(extra="allow")


class CalibrationAuditReport(BaseModel):
    """Safety-critical calibration and failure case autopsy report."""
    schema_version: str = Field(default="2.0.0")
    dataset_name: str = Field(..., description="Evaluated benchmark dataset title")
    split: str = Field(..., description="Dataset split evaluated (fit on val only, scored on test)")
    sample_count: int = Field(..., gt=0, description="Total evaluated samples")
    uncalibrated_ece: float = Field(..., description="Expected Calibration Error before calibration")
    calibrated_ece: float = Field(..., description="Expected Calibration Error after calibration")
    uncalibrated_brier: float = Field(..., description="Brier score before calibration")
    calibrated_brier: float = Field(..., description="Brier score after calibration")
    temperature: Optional[float] = Field(default=None, description="Optimal validation temperature T")
    worst_cases: List[Dict[str, Any]] = Field(default_factory=list, description="Top cases with highest loss/error")
    high_confidence_wrong_cases: List[Dict[str, Any]] = Field(default_factory=list, description="Critical silent failures (conf >= 0.75 and wrong)")
    low_confidence_correct_cases: List[Dict[str, Any]] = Field(default_factory=list, description="Underconfident correct cases (conf < 0.50 and correct)")
    common_failure_categories: Dict[str, int] = Field(default_factory=dict, description="Frequency counts by root cause")
    classwise_ece: Optional[Dict[str, float]] = Field(default=None, description="Class-wise calibration error")
    model_config = ConfigDict(extra="allow")


class DerivedMetricsTraceability(BaseModel):
    water_pct: float = 0.0
    vegetation_pct: float = 0.0
    built_up_pct: float = 0.0
    water_body_pct: float = 0.0
    vegetation_cover_pct: float = 0.0
    built_up_density_pct: float = 0.0
    bare_soil_pct: float = 0.0
    mean_ndvi: float = 0.0
    mean_ndwi: float = 0.0
    mean_ndbi: float = 0.0
    is_geotiff: bool = False
    model_config = ConfigDict(extra="allow")

    def __init__(self, **data):
        if "water_pct" in data and "water_body_pct" not in data:
            data["water_body_pct"] = data["water_pct"]
        elif "water_body_pct" in data and "water_pct" not in data:
            data["water_pct"] = data["water_body_pct"]
        if "vegetation_pct" in data and "vegetation_cover_pct" not in data:
            data["vegetation_cover_pct"] = data["vegetation_pct"]
        elif "vegetation_cover_pct" in data and "vegetation_pct" not in data:
            data["vegetation_pct"] = data["vegetation_cover_pct"]
        if "built_up_pct" in data and "built_up_density_pct" not in data:
            data["built_up_density_pct"] = data["built_up_pct"]
        elif "built_up_density_pct" in data and "built_up_pct" not in data:
            data["built_up_pct"] = data["built_up_density_pct"]
        super().__init__(**data)


class CheckpointProvenanceTraceability(BaseModel):
    model_name: str = "RSVqaFusionNetwork"
    checkpoint_path: Optional[str] = None
    path: Optional[str] = None
    sha256: Optional[str] = None
    sha256_hash: Optional[str] = None
    param_count: Optional[int] = None
    parameter_count: Optional[int] = None
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    model_config = ConfigDict(extra="allow")

    def __init__(self, **data):
        if "checkpoint_path" in data and not data.get("path"):
            data["path"] = data["checkpoint_path"]
        elif "path" in data and not data.get("checkpoint_path"):
            data["checkpoint_path"] = data["path"]
        if "param_count" in data and not data.get("parameter_count"):
            data["parameter_count"] = data["param_count"]
        elif "parameter_count" in data and not data.get("param_count"):
            data["param_count"] = data["parameter_count"]
        if "sha256" in data and not data.get("sha256_hash"):
            data["sha256_hash"] = data["sha256"]
        elif "sha256_hash" in data and not data.get("sha256"):
            data["sha256"] = data["sha256_hash"]
        super().__init__(**data)


class PreprocessingTraceability(BaseModel):
    radiometric_scaling: str = "standard_uint8_0_to_1"
    normalizer: str = "GeospatialNormalizer.compute_spectral_breakdown"
    input_shape: List[int] = Field(default_factory=list)
    target_resolution: List[int] = Field(default_factory=lambda: [224, 224])
    interpolation: str = "bilinear"
    channels_extracted: int = 3
    model_config = ConfigDict(extra="allow")


class EvidencePackage(BaseModel):
    """
    Comprehensive machine-readable evidence package grounding a remote-sensing answer.
    Directly implements Stage 7 ten-point traceability contract.
    """
    schema_version: str = Field(default="2.0.0")
    package_id: str = Field(..., description="Unique evidence package UUID")
    query: str = Field(..., description="Original user domain question")
    answer_text: str = Field(default="", description="Synthesized natural language answer")

    # 1. Source Image
    source_image: SourceImageTraceability = Field(..., description="Reference to source raster")
    # 2. Bands / Features Used
    bands_used: List[str] = Field(..., description="Specific spectral/radar bands utilized")
    # 3. Spatial Region
    spatial_region: SpatialRegionTraceability = Field(..., description="Geospatial footprint")
    # 4. Model Output
    model_output: ModelOutputTraceability = Field(..., description="Neural model prediction details")
    # 5. Confidence & Calibration Information
    confidence_and_calibration: ConfidenceCalibrationTraceability = Field(..., description="Confidence metrics")
    confidence_info: Optional[ConfidenceCalibrationTraceability] = None
    # 6. Derived Metrics (Genuine raster math)
    derived_metrics: DerivedMetricsTraceability = Field(..., description="Radiometric indices")
    # 7. Timestamp
    timestamp_utc: str = Field(..., description="ISO 8601 UTC execution timestamp")
    # 8. Checkpoint Provenance
    checkpoint_provenance: CheckpointProvenanceTraceability = Field(..., description="Checkpoint provenance")
    checkpoint_info: Optional[CheckpointProvenanceTraceability] = None
    # 9. Preprocessing
    preprocessing: PreprocessingTraceability = Field(..., description="Radiometric scaling and normalizer")
    preprocessing_info: Optional[PreprocessingTraceability] = None
    # 10. Warnings
    warnings: List[str] = Field(default_factory=list, description="Advisory flags")

    # Granular evidence items
    evidence_items: List[EvidenceItem] = Field(default_factory=list, description="Atomic evidence components")
    model_config = ConfigDict(extra="allow")

    def __init__(self, **data):
        # Sync aliases
        if "confidence_info" in data and "confidence_and_calibration" not in data:
            data["confidence_and_calibration"] = data["confidence_info"]
        elif "confidence_and_calibration" in data and "confidence_info" not in data:
            data["confidence_info"] = data["confidence_and_calibration"]

        if "checkpoint_info" in data and "checkpoint_provenance" not in data:
            data["checkpoint_provenance"] = data["checkpoint_info"]
        elif "checkpoint_provenance" in data and "checkpoint_info" not in data:
            data["checkpoint_info"] = data["checkpoint_provenance"]

        if "preprocessing_info" in data and "preprocessing" not in data:
            data["preprocessing"] = data["preprocessing_info"]
        elif "preprocessing" in data and "preprocessing_info" not in data:
            data["preprocessing_info"] = data["preprocessing"]
        super().__init__(**data)


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
class BenchmarkMetadata(BaseModel):
    """Metadata specification for an official remote sensing benchmark dataset."""
    schema_version: str = Field(default="2.0.0")
    benchmark_id: str = Field(..., description="Canonical benchmark identifier: e.g. levir_cd, sen12ms, indian_pines")
    dataset_name: str = Field(..., description="Official dataset title")
    official_source: str = Field(..., description="Primary publication, institution, or repository URL")
    citation: str = Field(..., description="Standard academic BibTeX/text citation")
    license_terms: str = Field(..., description="Open data license: e.g. CC-BY-4.0, ODC-BY, MIT, Academic Only")
    task: Literal[
        "change_detection",
        "multimodal_fusion",
        "hyperspectral_classification",
        "vqa",
        "visual_grounding",
        "multilabel_landcover"
    ] = Field(..., description="Target machine learning task category")
    modality: Literal[
        "optical_bitemporal",
        "optical_sar",
        "hyperspectral",
        "optical_multispectral",
        "sar",
        "optical",
        "rgb"
    ] = Field(..., description="Sensor data modality")
    sensors: List[str] = Field(default_factory=list, description="Sensor platforms: e.g. ['Sentinel-2', 'Sentinel-1']")
    spatial_resolution_meters: Optional[float] = Field(default=None, description="Ground sampling distance (GSD) in meters")
    split_definitions: Dict[str, Any] = Field(default_factory=dict, description="Specifications for train, val, and test partitions")
    label_schema: Dict[Any, Any] = Field(default_factory=dict, description="Class labels and index mappings")
    expected_metrics: List[str] = Field(default_factory=list, description="Standard metrics published on this benchmark")
    anti_leakage_policy: str = Field(default="Strict split isolation; test evaluated strictly once", description="Applicable split isolation policy")
    model_config = ConfigDict(extra="allow")


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
    model_name: Optional[str] = Field(default=None, description="Evaluated specialist model architecture name")
    checkpoint_path: Optional[str] = Field(default=None, description="Path to evaluated frozen checkpoint")
    checkpoint_hash: Optional[str] = Field(default=None, description="Cryptographic SHA-256 digest of checkpoint")
    preprocessing_summary: Optional[Dict[str, Any]] = Field(default=None, description="Radiometric scaling and normalizer summary")
    per_class_metrics: Optional[Dict[str, Dict[str, float]]] = Field(default=None, description="Per-class metric breakdown")
    failures_count: int = Field(default=0, ge=0, description="Number of failure cases diagnosed during evaluation")
    failure_cases: List[Any] = Field(default_factory=list, description="Sample FailureCase objects recorded")
    calibration_metrics: Optional[Dict[str, float]] = Field(default=None, description="ECE or confidence calibration stats if available")
    limitations: List[str] = Field(default_factory=list, description="Known model/benchmark domain limitations")
    comparison_baseline: Optional[Dict[str, Any]] = Field(default=None, description="Compatible reference baseline stats if compared")
    provenance_fingerprint: Optional[str] = Field(default=None, description="16-char deterministic execution fingerprint")
    model_config = ConfigDict(extra="allow")


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
        "seasonal_change",
        "small_object_miss",
        "boundary_error",
        "spatial_boundary_confusion",
        "spectral_metamerism",
        "rare_class_starvation",
        "water_absorption_noise",
        "false_positive",
        "false_negative",
        "other"
    ] = Field(..., description="Root-cause classification of failure")
    severity: Literal["low", "medium", "high", "critical"] = Field(default="medium")
    explanation: str = Field(..., description="Technical autopsy explaining why failure occurred")
    mitigation: Optional[str] = Field(default=None, description="Proposed algorithmic or data fix")
    confidence_score: Optional[float] = Field(default=None, description="Confidence score if applicable")
    model_config = ConfigDict(extra="allow")

