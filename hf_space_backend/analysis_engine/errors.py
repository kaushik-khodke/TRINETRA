"""
TRINETRA Analysis Engine — Error Taxonomy & Failure Modes
Categorizes analysis failures clearly so data/network/pre-processing issues
are never misreported as general model or system crashes.
"""

from enum import Enum
from typing import Optional, Dict, Any


class AnalysisErrorCode(str, Enum):
    INPUT_FAILURE = "INPUT_FAILURE"
    DATA_FAILURE = "DATA_FAILURE"
    PREPROCESSING_FAILURE = "PREPROCESSING_FAILURE"
    MODEL_FAILURE = "MODEL_FAILURE"
    RESOURCE_FAILURE = "RESOURCE_FAILURE"
    REASONING_FAILURE = "REASONING_FAILURE"
    ARTIFACT_FAILURE = "ARTIFACT_FAILURE"


class AnalysisEngineException(Exception):
    """Base exception for all EO analysis engine errors."""
    def __init__(
        self,
        code: AnalysisErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        recoverable: bool = False
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.recoverable = recoverable

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.code.value,
            "message": self.message,
            "details": self.details,
            "recoverable": self.recoverable,
        }


class InputFailureError(AnalysisEngineException):
    """Raised when request parameters, AOI geometry, or mode configurations are invalid."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(AnalysisErrorCode.INPUT_FAILURE, message, details, recoverable=True)


class DataFailureError(AnalysisEngineException):
    """Raised when STAC assets, local rasters, or bands cannot be found or accessed."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(AnalysisErrorCode.DATA_FAILURE, message, details, recoverable=False)


class PreprocessingFailureError(AnalysisEngineException):
    """Raised when raster reprojection, grid alignment, or normalization fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(AnalysisErrorCode.PREPROCESSING_FAILURE, message, details, recoverable=False)


class ModelFailureError(AnalysisEngineException):
    """Raised when deep learning inference or specialist execution throws an error."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(AnalysisErrorCode.MODEL_FAILURE, message, details, recoverable=False)


class ResourceFailureError(AnalysisEngineException):
    """Raised when GPU VRAM limits, memory budgets, or queue timeouts are exceeded."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(AnalysisErrorCode.RESOURCE_FAILURE, message, details, recoverable=True)


class ReasoningFailureError(AnalysisEngineException):
    """Raised when LLM reasoning fails schema constraints or produces hallucinations."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(AnalysisErrorCode.REASONING_FAILURE, message, details, recoverable=True)


class ArtifactFailureError(AnalysisEngineException):
    """Raised when writing output rasters, GeoJSONs, or preview images fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(AnalysisErrorCode.ARTIFACT_FAILURE, message, details, recoverable=False)
