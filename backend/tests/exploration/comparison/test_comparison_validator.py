"""
TRINETRA / Shanetra Geospatial Exploration Engine
Unit Tests: Comparison Validator
Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
"""

import pytest
from exploration.comparison.models import ComparisonMode
from exploration.comparison.validator import ComparisonValidator
from exploration.temporal.normalizer import ObservationSummary


def test_comparison_self_rejection():
    obs = ObservationSummary(
        id="obs_same",
        collection="sentinel-2-l2a",
        datetime="2026-03-01T00:00:00Z",
        bbox=[79.0, 21.0, 79.2, 21.2],
    )
    res = ComparisonValidator.validate(obs, obs)
    assert not res.compatible
    assert "itself" in res.errors[0]


def test_comparison_disjoint_footprints():
    obs_a = ObservationSummary(
        id="obs_a",
        collection="sentinel-2-l2a",
        datetime="2026-03-01T00:00:00Z",
        bbox=[78.0, 20.0, 78.5, 20.5],
    )
    obs_b = ObservationSummary(
        id="obs_b",
        collection="sentinel-2-l2a",
        datetime="2026-03-10T00:00:00Z",
        bbox=[85.0, 25.0, 85.5, 25.5],
    )
    res = ComparisonValidator.validate(obs_a, obs_b)
    assert not res.compatible
    assert "no spatial overlap" in res.errors[0]
    assert res.spatial_overlap_pct == 0.0


def test_comparison_compatible_overlap():
    obs_a = ObservationSummary(
        id="obs_a",
        collection="sentinel-2-l2a",
        datetime="2026-03-01T00:00:00Z",
        bbox=[79.0, 21.0, 79.5, 21.5],
    )
    obs_b = ObservationSummary(
        id="obs_b",
        collection="sentinel-2-l2a",
        datetime="2026-03-16T00:00:00Z",
        bbox=[79.1, 21.0, 79.5, 21.5],  # High overlap
    )
    res = ComparisonValidator.validate(obs_a, obs_b)
    assert res.compatible
    assert res.temporal_delta_days == 15.0
    assert res.spatial_overlap_pct is not None
    assert res.spatial_overlap_pct > 50.0
