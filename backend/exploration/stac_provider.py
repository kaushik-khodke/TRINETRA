"""
TRINETRA / Shanetra Geospatial Exploration Engine
STAC Provider — SpatioTemporal Asset Catalog Client
Phase 2: Discovers real Earth-observation products (Sentinel-2, Copernicus CDSE) with strict timeouts and failure tolerance.
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any
import requests

from exploration.models import EOItem, EOAsset
from exploration.schemas import ExploreSearchRequest
from exploration.providers import EODataProvider, ProviderCapabilities
from exploration.cache import search_cache, temporal_search_cache, build_temporal_cache_key
from exploration.temporal.normalizer import ObservationSummary, ObservationNormalizer
from exploration.temporal.search import TemporalSearchRequest
from exploration.temporal.sorter import TemporalSorter
from exploration.aoi.geometry import geometry_hash

logger = logging.getLogger("exploration.stac")

DEFAULT_COPERNICUS_STAC_URL = "https://stac.dataspace.copernicus.eu/v1"
CONNECT_TIMEOUT_SEC = 5.0
READ_TIMEOUT_SEC = 10.0


class STACProvider(EODataProvider):
    """Client for querying STAC-compliant satellite catalogs (Copernicus CDSE / ISRO)."""

    def __init__(self, endpoint_url: Optional[str] = None):
        self.endpoint_url = endpoint_url or os.environ.get("COPERNICUS_STAC_URL", DEFAULT_COPERNICUS_STAC_URL).rstrip("/")
        self._search_url = f"{self.endpoint_url}/search"

    @property
    def provider_name(self) -> str:
        return "copernicus"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_intersects=True,
            supports_bbox=True,
            supports_datetime=True,
            supports_cql2=False,
            supports_query=True,
            supports_sort=True,
            supports_fields=True,
            supports_thumbnails=True,
            supports_asset_urls=True,
        )


    def status(self) -> str:
        """Lightweight health probe for STAC endpoint."""
        try:
            resp = requests.get(
                self.endpoint_url,
                timeout=(CONNECT_TIMEOUT_SEC, READ_TIMEOUT_SEC),
                headers={"Accept": "application/json"},
            )
            return "available" if resp.status_code == 200 else "degraded"
        except Exception:
            return "offline"

    def search(self, request: ExploreSearchRequest) -> List[EOItem]:
        """Queries the STAC catalog and normalizes returned items into standard EOItem models."""
        cache_key = f"stac_search:{request.bbox}:{request.datetime_start}:{request.datetime_end}:{request.collections}:{request.limit}"
        cached = search_cache.get(cache_key)
        if cached is not None:
            return cached

        # Build STAC search payload
        payload: Dict[str, Any] = {"limit": min(request.limit, 50)}

        if request.bbox:
            payload["bbox"] = request.bbox

        if request.collections:
            payload["collections"] = request.collections
        else:
            payload["collections"] = ["ccm-optical"]

        if request.datetime_start and request.datetime_end:
            payload["datetime"] = f"{request.datetime_start}/{request.datetime_end}"
        elif request.datetime_start:
            payload["datetime"] = f"{request.datetime_start}/.."

        try:
            resp = requests.post(
                self._search_url,
                json=payload,
                headers={"Content-Type": "application/json", "Accept": "application/geo+json"},
                timeout=(CONNECT_TIMEOUT_SEC, READ_TIMEOUT_SEC),
            )
            if resp.status_code != 200:
                logger.warning(f"[STACProvider] STAC search HTTP {resp.status_code}: {resp.text[:200]}")
                return []

            data = resp.json()
            features = data.get("features", [])
            items = [self.normalize_stac_item(f) for f in features]
            items = [i for i in items if i is not None]

            search_cache.set(cache_key, items, ttl_seconds=300.0)
            return items

        except requests.exceptions.Timeout:
            logger.warning(f"[STACProvider] Timeout querying STAC endpoint {self._search_url}")
            return []
        except requests.exceptions.ConnectionError:
            logger.warning(f"[STACProvider] Connection error querying STAC endpoint {self._search_url}")
            return []
        except Exception as e:
            logger.error(f"[STACProvider] Unexpected STAC search error: {e}")
            return []

    def search_temporal(self, request: TemporalSearchRequest) -> List[ObservationSummary]:
        """
        Executes a multi-temporal search against the STAC endpoint with bounds,
        cloud-cover filtering, and returns normalized ObservationSummary instances.
        """
        aoi_hash = geometry_hash(request.aoi) if request.aoi else "global"
        cache_key = build_temporal_cache_key(
            aoi_hash=aoi_hash,
            start_dt=request.start_datetime,
            end_dt=request.end_datetime,
            collections=request.collections,
            cloud_max=request.cloud_cover_max,
            sort=request.sort,
            limit=request.limit,
        )
        cached = temporal_search_cache.get(cache_key)
        if cached is not None:
            return cached

        # Attempt STAC query via direct HTTP POST with standard STAC API schema
        payload: Dict[str, Any] = {
            "limit": min(request.limit, 100),
            "collections": request.collections or ["sentinel-2-l2a"],
            "datetime": f"{request.start_datetime}/{request.end_datetime}",
        }
        if request.aoi:
            payload["intersects"] = request.aoi
        if request.cloud_cover_max is not None:
            payload["query"] = {"eo:cloud_cover": {"lte": request.cloud_cover_max}}

        try:
            resp = requests.post(
                self._search_url,
                json=payload,
                headers={"Content-Type": "application/json", "Accept": "application/geo+json"},
                timeout=(CONNECT_TIMEOUT_SEC, READ_TIMEOUT_SEC),
            )
            if resp.status_code != 200:
                logger.warning(f"[STACProvider] STAC temporal search HTTP {resp.status_code}: {resp.text[:200]}")
                return []

            data = resp.json()
            features = data.get("features", [])
            summaries = [ObservationNormalizer.to_summary(f) for f in features]
            summaries = [s for s in summaries if s is not None]

            # Apply deterministic sorting and deduplication
            sorted_summaries = TemporalSorter.sort_and_deduplicate(summaries, sort_order=request.sort)
            temporal_search_cache.set(cache_key, sorted_summaries, ttl_seconds=300.0)
            return sorted_summaries

        except requests.exceptions.Timeout:
            logger.warning(f"[STACProvider] Timeout querying STAC endpoint {self._search_url}")
            return []
        except requests.exceptions.ConnectionError:
            logger.warning(f"[STACProvider] Connection error querying STAC endpoint {self._search_url}")
            return []
        except Exception as e:
            logger.error(f"[STACProvider] Unexpected STAC temporal search error: {e}")
            return []

    def get_item(self, item_id: str) -> Optional[EOItem]:

        """Retrieves a single STAC Item by ID."""
        url = f"{self.endpoint_url}/collections/SENTINEL-2/items/{item_id}"
        try:
            resp = requests.get(url, timeout=(CONNECT_TIMEOUT_SEC, READ_TIMEOUT_SEC))
            if resp.status_code == 200:
                return self.normalize_stac_item(resp.json())
        except Exception:
            pass
        return None

    def get_asset(self, asset_id: str) -> Optional[EOAsset]:
        # Remote assets are referenced via their respective EOItem
        return None

    def get_metadata(self, asset_id: str) -> Optional[Dict[str, Any]]:
        return None

    @staticmethod
    def normalize_stac_item(feature: Dict[str, Any]) -> Optional[EOItem]:
        """Converts a GeoJSON STAC Item dictionary into our internal normalized EOItem structure."""
        if not isinstance(feature, dict):
            return None

        item_id = feature.get("id")
        if not item_id:
            return None

        properties = feature.get("properties", {})
        dt = properties.get("datetime") or properties.get("start_datetime") or "2026-01-01T00:00:00Z"
        cloud = properties.get("eo:cloud_cover", properties.get("cloudCover", None))
        collection = feature.get("collection", "sentinel-2-l2a")
        bbox = feature.get("bbox", [-180.0, -90.0, 180.0, 90.0])

        # Parse Assets
        raw_assets = feature.get("assets", {})
        assets_dict: Dict[str, EOAsset] = {}
        thumb_url = None

        for a_key, a_val in raw_assets.items():
            if not isinstance(a_val, dict):
                continue
            href = a_val.get("href", "")
            roles = a_val.get("roles", [])
            media_type = a_val.get("type", "image/tiff")
            title = a_val.get("title", a_key)

            if "thumbnail" in roles or a_key == "thumbnail":
                thumb_url = href

            assets_dict[a_key] = EOAsset(
                id=a_key,
                href=href,
                media_type=media_type,
                role=roles[0] if roles else "visual",
                title=title,
                bands=a_val.get("eo:bands", None),
            )

        return EOItem(
            id=item_id,
            collection=collection,
            datetime=dt,
            bbox=bbox,
            geometry=feature.get("geometry"),
            cloud_cover=float(cloud) if cloud is not None else None,
            assets=assets_dict,
            provider="copernicus",
            thumbnail_url=thumb_url,
            properties=properties,
            source_url=feature.get("links", [{}])[0].get("href") if feature.get("links") else None,
        )
