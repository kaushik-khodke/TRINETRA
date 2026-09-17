"""
TRINETRA Calibration, Uncertainty, and Failure Analysis Framework (Stage 9)
Governed by 09_STAGE_9_CALIBRATION.md and NON_NEGOTIABLE_PRINCIPLES.md.
"""

try:
    from backend.calibration.calibrator import (
        TemperatureScaler,
        IsotonicCalibrator,
        PlattScaler,
        ReliabilityDiagram,
        compute_brier_score,
        compute_classwise_ece
    )
    from backend.calibration.uncertainty import (
        ConfidenceSemantics,
        UncertaintyDecompositionEngine
    )
    from backend.calibration.failure_miner import (
        FailureMiner
    )
except ImportError:
    from calibration.calibrator import (
        TemperatureScaler,
        IsotonicCalibrator,
        PlattScaler,
        ReliabilityDiagram,
        compute_brier_score,
        compute_classwise_ece
    )
    from calibration.uncertainty import (
        ConfidenceSemantics,
        UncertaintyDecompositionEngine
    )
    from calibration.failure_miner import (
        FailureMiner
    )


__all__ = [
    "TemperatureScaler",
    "IsotonicCalibrator",
    "PlattScaler",
    "ReliabilityDiagram",
    "compute_brier_score",
    "compute_classwise_ece",
    "ConfidenceSemantics",
    "UncertaintyDecompositionEngine",
    "FailureMiner"
]
