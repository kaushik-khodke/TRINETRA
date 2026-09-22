"""
TRINETRA Phase 8 — Structured Reporting & Evidence Package Subsystem.
Claim-to-evidence validation, server-side presentation rendering, SHA-256 manifests, and tamper-evident ZIP packaging.
"""

from .sections import ReportSectionFactory
from .validator import ReportValidator, ClaimEvidenceError, CausalAttributionWarning
from .manifest import ReportManifestGenerator
from .map_snapshot import MapSnapshotGenerator
from .renderer import ReportPresentationRenderer
from .builder import ReportBuilder
from .exporter import ReportPackageExporter

__all__ = [
    "ReportSectionFactory",
    "ReportValidator",
    "ClaimEvidenceError",
    "CausalAttributionWarning",
    "ReportManifestGenerator",
    "MapSnapshotGenerator",
    "ReportPresentationRenderer",
    "ReportBuilder",
    "ReportPackageExporter",
]
