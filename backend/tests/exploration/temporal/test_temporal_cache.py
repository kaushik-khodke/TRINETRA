"""
TRINETRA / Shanetra Geospatial Exploration Engine
Unit Tests: Temporal Search Cache
Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
"""

import pytest
from exploration.cache import temporal_search_cache, build_temporal_cache_key
from exploration.temporal.normalizer import ObservationSummary


def test_temporal_cache_hit_and_eviction():
    temporal_search_cache.clear()

    key1 = build_temporal_cache_key(
        aoi_hash="hash_123",
        start_dt="2026-01-01T00:00:00Z",
        end_dt="2026-06-01T00:00:00Z",
        collections=["sentinel-2-l2a"],
        cloud_max=20.0,
        sort="datetime_desc",
        limit=25,
    )

    dummy_results = [
        ObservationSummary(
            id="test_obs",
            collection="sentinel-2-l2a",
            datetime="2026-03-01T00:00:00Z",
        )
    ]

    assert temporal_search_cache.get(key1) is None
    temporal_search_cache.set(key1, dummy_results, ttl_seconds=60.0)

    cached = temporal_search_cache.get(key1)
    assert cached is not None
    assert len(cached) == 1
    assert cached[0].id == "test_obs"
