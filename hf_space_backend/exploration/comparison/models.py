"""
TRINETRA / Shanetra Geospatial Exploration Engine
Comparison Models & Compatibility Contracts
Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from exploration.temporal.normalizer import ObservationSummary


class ComparisonMode(str, Enum):
    SIDE_BY_SIDE = "side_by_side"
    SPLIT = "split"
    OPACITY = "opacity"


class ComparisonValidationRequest(BaseModel):
    """Request to validate pairing compatibility between two observations."""
    observation_a_id: str = Field(..., min_length=1, max_length=128)
    observation_b_id: str = Field(..., min_length=1, max_length=128)
    mode: ComparisonMode = Field(default=ComparisonMode.SPLIT)


class ComparisonValidationResponse(BaseModel):
    """Validation response with compatibility status, temporal delta, and spatial overlap."""
    compatible: bool
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    observation_a: Optional[ObservationSummary] = None
    observation_b: Optional[ObservationSummary] = None
    temporal_delta_days: Optional[float] = None
    spatial_overlap_pct: Optional[float] = None
