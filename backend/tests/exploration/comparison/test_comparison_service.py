"""
TRINETRA / Shanetra Geospatial Exploration Engine
Unit Tests: Comparison Service
Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
"""

import pytest
from exploration.comparison.models import ComparisonValidationRequest, ComparisonMode
from exploration.comparison.service import ComparisonService


def test_validate_nonexistent_observations():
    req = ComparisonValidationRequest(
        observation_a_id="nonexistent_a",
        observation_b_id="nonexistent_b",
        mode=ComparisonMode.SPLIT,
    )
    res = ComparisonService.validate_comparison(req)
    assert not res.compatible
    assert len(res.errors) > 0
