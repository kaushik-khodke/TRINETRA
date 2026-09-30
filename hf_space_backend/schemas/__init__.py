"""
TRINETRA — Typed Architecture Contracts Package
SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)
Exports typed Pydantic models for service boundaries, validation, evidence, and provenance.
"""

from .contracts import (
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

__all__ = [
    "InputAsset",
    "RasterMetadata",
    "AlignmentReport",
    "TaskRequest",
    "ModelRun",
    "QuantumModelRun",
    "Prediction",
    "MetricSet",
    "EvidenceItem",
    "ProvenanceRecord",
    "ValidationResult",
    "BenchmarkRun",
    "FailureCase"
]
