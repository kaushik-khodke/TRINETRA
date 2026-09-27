"""
TRINETRA Phase 6 — Tests for Temporal Trajectory & Persistence Analysis
"""

import pytest
from investigation.temporal.trajectory import TemporalTrajectoryAnalyzer
from investigation.temporal.persistence import PersistenceEvaluator
from investigation.temporal.recurrence import RecurrenceDetector


def test_temporal_trajectory_gradual_expansion():
    series = [
        {"date": "2025-01-01", "change_pct": 1.0, "ndvi": 0.60},
        {"date": "2025-04-01", "change_pct": 3.5, "ndvi": 0.50},
        {"date": "2025-08-01", "change_pct": 6.8, "ndvi": 0.40},
        {"date": "2025-12-01", "change_pct": 11.2, "ndvi": 0.30},
    ]
    trajectory = TemporalTrajectoryAnalyzer.analyze_trajectory(series)
    assert trajectory.is_monotonic is True
    assert trajectory.pattern in ["gradual_expansion", "persistent_transformation"]


def test_persistence_evaluator():
    observations = [
        {"id": "obs_1", "datetime": "2025-01-01T00:00:00Z"},
        {"id": "obs_2", "datetime": "2025-06-01T00:00:00Z"},
        {"id": "obs_3", "datetime": "2025-12-01T00:00:00Z"},
    ]
    presence_mask = [True, True, True]
    rep = PersistenceEvaluator.evaluate_region_persistence(
        region_id="r_01",
        observations=observations,
        presence_mask=presence_mask,
    )
    assert rep.persistence_ratio == 1.0
    assert rep.consecutive_presence == 3
    assert rep.duration_days > 300


def test_recurrence_detector_cyclical():
    # Seasonal oscillation pattern
    series = [
        {"date": "2024-01-01", "change_pct": 2.0},
        {"date": "2024-07-01", "change_pct": 15.0},
        {"date": "2025-01-01", "change_pct": 2.5},
        {"date": "2025-07-01", "change_pct": 14.5},
    ]
    rec = RecurrenceDetector.detect_recurrence(series)
    assert rec.is_cyclical is True
    assert rec.oscillation_count >= 1
