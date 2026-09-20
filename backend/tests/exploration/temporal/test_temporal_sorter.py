"""
TRINETRA / Shanetra Geospatial Exploration Engine
Unit Tests: Temporal Sorter & Resolver
Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
"""

import pytest
from exploration.temporal.normalizer import ObservationSummary
from exploration.temporal.sorter import TemporalSorter
from exploration.temporal.resolver import TemporalResolver


@pytest.fixture
def sample_observations():
    return [
        ObservationSummary(
            id="obs_1",
            collection="sentinel-2-l2a",
            datetime="2026-01-10T10:00:00Z",
            cloud_cover=25.0,
            platform="Sentinel-2A",
            bbox=[79.0, 21.0, 79.2, 21.2],
        ),
        ObservationSummary(
            id="obs_2",
            collection="sentinel-2-l2a",
            datetime="2026-02-15T10:00:00Z",
            cloud_cover=5.0,
            platform="Sentinel-2B",
            bbox=[79.0, 21.0, 79.2, 21.2],
        ),
        ObservationSummary(
            id="obs_3",
            collection="sentinel-2-l2a",
            datetime="2026-03-20T10:00:00Z",
            cloud_cover=40.0,
            platform="Sentinel-2A",
            bbox=[79.0, 21.0, 79.2, 21.2],
        ),
        ObservationSummary(
            id="obs_2",  # Duplicate ID
            collection="sentinel-2-l2a",
            datetime="2026-02-15T10:00:00Z",
            cloud_cover=5.0,
            platform="Sentinel-2B",
            bbox=[79.0, 21.0, 79.2, 21.2],
        ),
    ]


def test_sort_datetime_desc_and_deduplicate(sample_observations):
    res = TemporalSorter.sort_and_deduplicate(sample_observations, sort_order="datetime_desc")
    assert len(res) == 3
    assert res[0].id == "obs_3"
    assert res[1].id == "obs_2"
    assert res[2].id == "obs_1"


def test_sort_datetime_asc(sample_observations):
    res = TemporalSorter.sort_and_deduplicate(sample_observations, sort_order="datetime_asc")
    assert len(res) == 3
    assert res[0].id == "obs_1"
    assert res[2].id == "obs_3"


def test_sort_cloud_asc(sample_observations):
    res = TemporalSorter.sort_and_deduplicate(sample_observations, sort_order="cloud_asc")
    assert len(res) == 3
    assert res[0].id == "obs_2"  # cloud 5.0
    assert res[1].id == "obs_1"  # cloud 25.0
    assert res[2].id == "obs_3"  # cloud 40.0


def test_resolver_helpers(sample_observations):
    latest = TemporalResolver.resolve_latest(sample_observations)
    assert latest is not None
    assert latest.id == "obs_3"

    prev = TemporalResolver.resolve_previous(sample_observations, current_id="obs_3")
    assert prev is not None
    assert prev.id == "obs_2"

    nxt = TemporalResolver.resolve_next(sample_observations, current_id="obs_2")
    assert nxt is not None
    assert nxt.id == "obs_3"

    pair = TemporalResolver.resolve_pair(sample_observations)
    assert pair is not None
    assert pair[0].id == "obs_3"
    assert pair[1].id == "obs_2"
