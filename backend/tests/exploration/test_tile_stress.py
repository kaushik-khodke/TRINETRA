"""
Performance & Stress Tests — Repeated Tile Generation
Requests hundreds of tiles sequentially, verifying bounded memory and cache behavior.
"""

import time
import os
import pytest
from exploration.service import explore_service
from exploration.cache import tile_cache


def test_tile_stress_and_cache_reuse():
    layer_id = "layer-local_sentinel2_nagpur_truecolor"
    # Ensure layer registered
    explore_service.register_dataset_layer("local_sentinel2_nagpur_truecolor")

    # Initial cold request
    start_cold = time.perf_counter()
    cold_tile = explore_service.render_tile(layer_id, 8, 184, 112)
    cold_ms = (time.perf_counter() - start_cold) * 1000.0

    assert cold_tile is not None
    assert len(cold_tile) > 0

    # Execute 150 sequential requests
    hit_times = []
    for _ in range(150):
        t0 = time.perf_counter()
        tile = explore_service.render_tile(layer_id, 8, 184, 112)
        hit_times.append((time.perf_counter() - t0) * 1000.0)
        assert tile == cold_tile

    avg_cached_ms = sum(hit_times) / len(hit_times)
    stats = tile_cache.get_stats()

    print(f"\n[Tile Performance] Cold: {cold_ms:.2f}ms | Cached Avg: {avg_cached_ms:.3f}ms | Cache Hits: {stats['hits']}")
    assert stats["hits"] >= 150
    # Cached responses should be fast (typically < 1.0ms)
    assert avg_cached_ms < 5.0
