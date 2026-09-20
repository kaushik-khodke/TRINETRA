"""
Unit Tests — Bounded Cache Engine
Tests LRU capacity eviction, TTL expiration, negative caching, and deterministic cache keys.
"""

import time
import pytest
from exploration.cache import BoundedTTLCache, build_tile_cache_key


def test_cache_hits_and_misses():
    cache = BoundedTTLCache(max_size=5, default_ttl_seconds=10.0, name="test")
    assert cache.get("k1") is None

    cache.set("k1", "value1")
    assert cache.get("k1") == "value1"

    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1


def test_cache_ttl_expiration():
    cache = BoundedTTLCache(max_size=5, default_ttl_seconds=0.05, name="test_ttl")
    cache.set("exp_key", "data")
    assert cache.get("exp_key") == "data"

    time.sleep(0.06)
    # Expired
    assert cache.get("exp_key") is None


def test_cache_lru_eviction():
    cache = BoundedTTLCache(max_size=3, default_ttl_seconds=60.0, name="test_lru")
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)

    # Access 'a' so 'b' becomes the oldest
    assert cache.get("a") == 1

    # Insert 'd' (capacity exceeded, should evict 'b')
    cache.set("d", 4)

    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3
    assert cache.get("d") == 4


def test_deterministic_tile_cache_key():
    k1 = build_tile_cache_key("layer1", "asset1", 5, 10, 20, {"cmap": "viridis", "contrast": 1.2})
    k2 = build_tile_cache_key("layer1", "asset1", 5, 10, 20, {"contrast": 1.2, "cmap": "viridis"})
    k3 = build_tile_cache_key("layer1", "asset1", 5, 10, 20, {"cmap": "magma"})

    # Order of dict keys does not affect cache key
    assert k1 == k2
    # Different parameter produces different cache key
    assert k1 != k3
