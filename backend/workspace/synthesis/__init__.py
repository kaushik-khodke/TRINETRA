"""
TRINETRA Phase 8 — Intelligence Synthesis Subsystem.
Constructs evidence graphs, detects analytical conflicts, groups findings, and generates syntheses.
"""

from .conflicts import ConflictDetector, ConflictRecord
from .evidence import EvidenceGraphBuilder
from .findings import FindingClusterer
from .context import SynthesisContextExtractor
from .validator import SynthesisValidator, SynthesisValidationError
from .builder import WorkspaceSynthesizer

__all__ = [
    "ConflictDetector",
    "ConflictRecord",
    "EvidenceGraphBuilder",
    "FindingClusterer",
    "SynthesisContextExtractor",
    "SynthesisValidator",
    "SynthesisValidationError",
    "WorkspaceSynthesizer",
]
