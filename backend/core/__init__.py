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
    ProvenanceIntegrityError
)

__all__ = [
    "TRINETRABaseException",
    "InputValidationError",
    "GeospatialValidationError",
    "AlignmentMismatchError",
    "ModelCheckpointError",
    "ModalityResolutionError",
    "InferenceTimeoutError",
    "ProvenanceIntegrityError"
]
