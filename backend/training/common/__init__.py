"""
TRINETRA / SatQuery AI — Shared Training Infrastructure
Common utilities for metrics, reproducible seeding, profiling, checkpointing, and reporting.
"""

from .seed import set_seed
from .profiling import HardwareProfile, get_profile_config
from .checkpoint import CheckpointManager
from .reporting import TrainingReporter
from .metrics import (
    multilabel_metrics,
    vqa_metrics,
    grounding_metrics,
    calculate_iou,
    change_metrics,
    fusion_metrics,
    hyperspectral_metrics
)
from .dataset_utils import verify_real_dataset, verify_split_leakage
