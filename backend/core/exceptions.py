"""
TRINETRA — Domain Exception Hierarchy
SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)
Structured domain exceptions that cleanly translate into typed FailureCase
records and standardized API error payloads.
"""

from typing import Dict, Any, Optional, Literal


class TRINETRABaseException(Exception):
    """Base exception for all TRINETRA runtime, validation, and inference failures."""

    def __init__(
        self,
        message: str,
        error_code: str = "ERR_GENERIC_FAILURE",
        context: Optional[Dict[str, Any]] = None,
        severity: Literal["low", "medium", "high", "critical"] = "medium",
        mitigation: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.severity = severity
        self.mitigation = mitigation or "Inspect logs and verify input parameters."

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity,
            "context": self.context,
            "mitigation": self.mitigation
        }


class InputValidationError(TRINETRABaseException):
    """Raised when an uploaded file violates size, extension, or security limits."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="ERR_INPUT_VALIDATION",
            context=context,
            severity="medium",
            mitigation="Ensure file format is GeoTIFF/PNG/H5 and size is under 500 MB."
        )


class GeospatialValidationError(TRINETRABaseException):
    """Raised when a raster has missing or corrupt geospatial reference headers."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="ERR_GEOSPATIAL_METADATA",
            context=context,
            severity="high",
            mitigation="Verify raster has valid CRS projection and affine transform tags."
        )


class AlignmentMismatchError(TRINETRABaseException):
    """Raised when bi-temporal or multimodal rasters cannot be spatially coregistered."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="ERR_SPATIAL_MISALIGNMENT",
            context=context,
            severity="high",
            mitigation="Reproject source rasters to a shared reference grid before comparison."
        )


class ModelCheckpointError(TRINETRABaseException):
    """Raised when a neural network checkpoint is missing, corrupted, or key-incompatible."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="ERR_CHECKPOINT_INTEGRITY",
            context=context,
            severity="critical",
            mitigation="Verify checkpoint path, architecture parameter keys, and SHA-256 hash."
        )


class ModalityResolutionError(TRINETRABaseException):
    """Raised when input assets cannot be mapped to the required task modalities."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="ERR_MODALITY_RESOLUTION",
            context=context,
            severity="medium",
            mitigation="Provide required sensor inputs (e.g. Optical RGB + SAR VV/VH for fusion)."
        )


class InferenceTimeoutError(TRINETRABaseException):
    """Raised when model or quantum circuit simulation exceeds execution timeout."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="ERR_INFERENCE_TIMEOUT",
            context=context,
            severity="high",
            mitigation="Reduce batch/crop size or execute on accelerated hardware device."
        )


class ProvenanceIntegrityError(TRINETRABaseException):
    """Raised when an artifact or benchmark run lacks verified cryptographic provenance."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="ERR_PROVENANCE_INTEGRITY",
            context=context,
            severity="critical",
            mitigation="Re-run pipeline ensuring git commit, environment hash, and input hashes are recorded."
        )


class DatasetValidationError(TRINETRABaseException):
    """Raised when a benchmark dataset has missing files, invalid pairing, or corrupted rasters."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="ERR_DATASET_VALIDATION",
            context=context,
            severity="high",
            mitigation="Inspect dataset directory, verify paired samples in A/ and B/, and check image dimensions."
        )


class DatasetLeakageError(TRINETRABaseException):
    """Raised when sample overlap is detected between train, validation, or test splits."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="ERR_DATASET_LEAKAGE",
            context=context,
            severity="critical",
            mitigation="Ensure train, val, and test splits are strictly disjoint sets with zero shared asset IDs."
        )


class SecurityViolationError(TRINETRABaseException):
    """Raised when an operation violates security policy (path traversal, zip bomb, unsafe upload)."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="ERR_SECURITY_VIOLATION",
            context=context,
            severity="critical",
            mitigation="Validate file name, paths, file magic bytes, and compression limits."
        )


class UnsafeDeserializationError(TRINETRABaseException):
    """Raised when an untrusted or unsafe serialized object/weight is encountered."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="ERR_UNSAFE_DESERIALIZATION",
            context=context,
            severity="critical",
            mitigation="Load weights using weights_only=True or safe tensor serialization formats."
        )


# Aliases for benchmark framework compatibility
DataLeakageError = DatasetLeakageError
ModelIntegrityError = ModelCheckpointError
InferenceError = InferenceTimeoutError
SecurityError = SecurityViolationError

