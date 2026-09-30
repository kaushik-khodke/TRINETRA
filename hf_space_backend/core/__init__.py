"""
TRINETRA — Core System Primitives & Exceptions Package
"""

from .exceptions import (
    TRINETRABaseException,
    InputValidationError,
    GeospatialValidationError,
    AlignmentMismatchError,
    ModelCheckpointError,
    ModalityResolutionError,
    InferenceTimeoutError,
    ProvenanceIntegrityError,
    DatasetValidationError,
    DatasetLeakageError
)

__all__ = [
    "TRINETRABaseException",
    "InputValidationError",
    "GeospatialValidationError",
    "AlignmentMismatchError",
    "ModelCheckpointError",
    "ModalityResolutionError",
    "InferenceTimeoutError",
    "ProvenanceIntegrityError",
    "DatasetValidationError",
    "DatasetLeakageError"
]

