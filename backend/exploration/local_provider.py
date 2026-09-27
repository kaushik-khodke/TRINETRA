"""
TRINETRA / Shanetra Geospatial Exploration Engine
Local Raster Provider
Phase 2: Indexes and serves local GeoTIFF fixtures and curated satellite samples deterministically.
"""

import os
import glob
from typing import List, Dict, Optional, Any
from datetime import datetime

from shapely.geometry import box, shape

from exploration.models import EOItem, EOAsset
from exploration.schemas import ExploreSearchRequest
from exploration.providers import EODataProvider, ProviderCapabilities
from exploration.policies import LayerPolicyEngine
from exploration.raster_service import RasterService
from exploration.temporal.normalizer import ObservationSummary, ObservationNormalizer
from exploration.temporal.search import TemporalSearchRequest
from exploration.temporal.sorter import TemporalSorter
from geospatial.validator import GeospatialValidator


class LocalRasterProvider(EODataProvider):
    """Local-first geospatial catalog indexing trusted GeoTIFFs and sample satellite rasters."""

    def __init__(self, data_dirs: Optional[List[str]] = None):
        if data_dirs is None:
            custom_dir = os.environ.get("TRINETRA_DATA_DIR") or os.environ.get("LOCAL_RASTER_DIR")
            self.data_dirs = [custom_dir] if (custom_dir and os.path.exists(custom_dir)) else []
        else:
            self.data_dirs = [d for d in data_dirs if os.path.exists(d)]

        self._index: Dict[str, EOItem] = {}
        self._asset_map: Dict[str, str] = {}  # asset_id -> local_filepath
        self._indexed = False

    @property
    def provider_name(self) -> str:
        return "local"

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_intersects=True,
            supports_bbox=True,
            supports_datetime=True,
            supports_cql2=False,
            supports_query=False,
            supports_sort=True,
            supports_fields=True,
            supports_thumbnails=True,
            supports_asset_urls=True,
        )

    def status(self) -> str:

        self._ensure_indexed()
        return "ready" if len(self._index) > 0 else "empty"

    def _ensure_indexed(self) -> None:
        """Lazily indexes local sample directories."""
        if self._indexed:
            return

        for d in self.data_dirs:
            if not os.path.exists(d):
                continue

            for root, _, files in os.walk(d):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext not in [".tif", ".tiff", ".geotiff"]:
                        continue

                    full_path = os.path.join(root, f)
                    asset_id = f"local_{os.path.splitext(f)[0].lower()}"

                    # Sanitize asset ID
                    if not LayerPolicyEngine.validate_safe_asset_id(asset_id):
                        continue

                    try:
                        source = RasterService.read_metadata(full_path, asset_id)
                        self._asset_map[asset_id] = full_path

                        # Create normalized EOAsset
                        asset = EOAsset(
                            id=asset_id,
                            href=f"/api/v1/explore/assets/{asset_id}",
                            media_type="image/tiff; application=geotiff",
                            role="visual",
                            title=source.sensor_name or f,
                            bands=[f"Band {i+1}" for i in range(source.bands)],
                            local_path=full_path,
                            is_cog=source.is_cog,
                        )

                        # Create normalized EOItem
                        item_id = f"item_{asset_id}"
                        now_str = datetime.utcnow().isoformat() + "Z"
                        item = EOItem(
                            id=item_id,
                            collection="local-rasters",
                            datetime=now_str,
                            bbox=source.bounds,
                            cloud_cover=0.0,
                            assets={asset_id: asset},
                            provider="local",
                            thumbnail_url=f"/api/v1/explore/tiles/{asset_id}/4/11/7.png",
                            properties={
                                "sensor": source.sensor_name,
                                "modality": source.modality,
                                "width": source.width,
                                "height": source.height,
                                "crs": source.crs,
                                "is_cog": source.is_cog,
                            },
                        )
                        self._index[item_id] = item
                    except Exception as e:
                        # Skip corrupted or unreadable fixture silently
                        pass

        self._indexed = True

    def reindex(self) -> int:
        """Forces re-indexing of all configured directories."""
        self._indexed = False
        self._index.clear()
        self._asset_map.clear()
        self._ensure_indexed()
        return len(self._index)

    def search(self, request: ExploreSearchRequest) -> List[EOItem]:
        """Searches indexed local rasters by bounding box and limits."""
        self._ensure_indexed()
        results: List[EOItem] = []

        for item in self._index.values():
            if request.bbox:
                # Check bounding box intersection
                q_min_lon, q_min_lat, q_max_lon, q_max_lat = request.bbox
                i_min_lon, i_min_lat, i_max_lon, i_max_lat = item.bbox

                if (
                    q_max_lon < i_min_lon
                    or q_min_lon > i_max_lon
                    or q_max_lat < i_min_lat
                    or q_min_lat > i_max_lat
                ):
                    continue

            results.append(item)
            if len(results) >= request.limit:
                break

        return results

    def search_temporal(self, request: TemporalSearchRequest) -> List[ObservationSummary]:
        """
        Searches indexed local rasters by AOI geometry intersection, temporal bounds,
        and cloud cover constraints.
        """
        self._ensure_indexed()
        aoi_shape = None
        if request.aoi:
            try:
                aoi_shape = shape(request.aoi)
            except Exception:
                aoi_shape = None

        matched_summaries: List[ObservationSummary] = []

        for item in self._index.values():
            # Spatial intersection check
            if aoi_shape:
                try:
                    item_geom = box(*item.bbox)
                    if not item_geom.intersects(aoi_shape):
                        continue
                except Exception:
                    pass

            # Cloud cover filter
            if request.cloud_cover_max is not None:
                if item.cloud_cover is not None and item.cloud_cover > request.cloud_cover_max:
                    continue

            # Convert to summary
            summary = ObservationNormalizer.to_summary(item)
            matched_summaries.append(summary)


        # Sort and deduplicate
        sorted_summaries = TemporalSorter.sort_and_deduplicate(
            matched_summaries, sort_order=request.sort
        )
        return sorted_summaries[: request.limit]

    def get_item(self, item_id: str) -> Optional[EOItem]:

        self._ensure_indexed()
        return self._index.get(item_id)

    def get_asset(self, asset_id: str) -> Optional[EOAsset]:
        self._ensure_indexed()
        for item in self._index.values():
            if asset_id in item.assets:
                return item.assets[asset_id]
        return None

    def get_local_path(self, asset_id: str) -> Optional[str]:
        self._ensure_indexed()
        return self._asset_map.get(asset_id)

    def get_metadata(self, asset_id: str) -> Optional[Dict[str, Any]]:
        self._ensure_indexed()
        path = self._asset_map.get(asset_id)
        if not path:
            return None
        source = RasterService.read_metadata(path, asset_id)
        return {
            "asset_id": source.asset_id,
            "crs": source.crs,
            "bounds": source.bounds,
            "width": source.width,
            "height": source.height,
            "bands": source.bands,
            "dtype": source.dtype,
            "nodata": source.nodata,
            "resolution": source.resolution,
            "sensor_name": source.sensor_name,
            "modality": source.modality,
            "is_cog": source.is_cog,
        }
