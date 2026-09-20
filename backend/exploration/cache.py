"""
TRINETRA / Shanetra Geospatial Exploration Engine
Bounded LRU & TTL Cache
Phase 2: In-memory bounded caching with explicit TTL, eviction policies, and negative caching.
"""

import time
import threading
from collections import OrderedDict
from typing import Any, Optional, Dict, Tuple


class BoundedTTLCache:
    """Thread-safe bounded in-memory cache with Least-Recently-Used (LRU) eviction and TTL expiry."""

    def __init__(self, max_size: int = 500, default_ttl_seconds: float = 600.0, name: str = "cache"):
        self.max_size = max(1, max_size)
        self.default_ttl = default_ttl_seconds
        self.name = name
        self._lock = threading.Lock()
        self._store: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Retrieves value if present and unexpired. Promotes key to most recently used."""
        with self._lock:
            if key not in self._store:
                self._misses += 1
                return None

            value, expiry = self._store[key]
            if time.time() > expiry:
                # Expired
                del self._store[key]
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._store.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """Stores key-value pair with designated TTL, evicting oldest item if capacity is exceeded."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expiry = time.time() + ttl

        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (value, expiry)

            # Evict LRU elements if over capacity
            while len(self._store) > self.max_size:
                self._store.popitem(last=False)

    def delete(self, key: str) -> bool:
        """Removes a key from the cache if present."""
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def clear(self) -> None:
        """Flushes all entries from this cache."""
        with self._lock:
            self._store.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Returns runtime hit/miss statistics and current size."""
        with self._lock:
            now = time.time()
            valid_entries = sum(1 for _, exp in self._store.values() if exp >= now)
            total = self._hits + self._misses
            hit_ratio = round(self._hits / total, 3) if total > 0 else 0.0
            return {
                "name": self.name,
                "current_size": len(self._store),
                "active_entries": valid_entries,
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_ratio": hit_ratio,
            }


# Dedicated caches with explicit sizing
tile_cache = BoundedTTLCache(max_size=1000, default_ttl_seconds=900.0, name="tiles")
metadata_cache = BoundedTTLCache(max_size=300, default_ttl_seconds=3600.0, name="metadata")
search_cache = BoundedTTLCache(max_size=100, default_ttl_seconds=300.0, name="search")
temporal_search_cache = BoundedTTLCache(max_size=200, default_ttl_seconds=300.0, name="temporal_search")
negative_cache = BoundedTTLCache(max_size=150, default_ttl_seconds=60.0, name="negative_404")


def build_tile_cache_key(
    layer_id: str,
    asset_id: str,
    z: int,
    x: int,
    y: int,
    params: Optional[Dict[str, Any]] = None,
) -> str:
    """Constructs a deterministic cache key encompassing layer, coordinates, and visualization settings."""
    param_str = ""
    if params:
        sorted_items = sorted((k, str(v)) for k, v in params.items())
        param_str = ":" + "&".join(f"{k}={v}" for k, v in sorted_items)
    return f"tile:{layer_id}:{asset_id}:{z}:{x}:{y}{param_str}"


def build_temporal_cache_key(
    aoi_hash: str,
    start_dt: str,
    end_dt: str,
    collections: Optional[list] = None,
    cloud_max: Optional[float] = None,
    sort: str = "datetime_desc",
    limit: int = 25,
) -> str:
    """Constructs a deterministic cache key for multi-temporal observation searches."""
    colls = ",".join(sorted(collections or []))
    cloud_str = f"{cloud_max:.1f}" if cloud_max is not None else "none"
    return f"temporal:{aoi_hash}:{start_dt}:{end_dt}:{colls}:{cloud_str}:{sort}:{limit}"

