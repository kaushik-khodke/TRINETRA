"""
TRINETRA / Shanetra Geospatial Exploration Engine
Explore Service — High-Level Coordinator
Phase 2: Coordinates catalog providers, layer governance, asset resolution, and tile generation.
"""

import time
import uuid
from typing import List, Dict, Optional, Any
from exploration.models import EOItem, EOAsset, ExploreLayer, RasterSource
from exploration.schemas import (
    ExploreSearchRequest,
    ExploreSearchResponse,
    EOItemResponse,
    EOAssetResponse,
    LayerResponse,
    RasterMetadataResponse,
    CatalogStatusResponse,
)
from exploration.local_provider import LocalRasterProvider
from exploration.stac_provider import STACProvider
from exploration.asset_resolver import AssetResolver
from exploration.raster_service import RasterService
from exploration.tile_service import TileService
from exploration.policies import LayerPolicyEngine
from exploration.cache import tile_cache, metadata_cache, search_cache, temporal_search_cache, build_temporal_cache_key
from exploration.temporal.normalizer import ObservationSummary, ObservationDetails, ObservationNormalizer
from exploration.temporal.search import TemporalSearchRequest, TemporalSearchResponse
from exploration.temporal.sorter import TemporalSorter
from exploration.aoi.validator import AOIValidator
from exploration.aoi.geometry import geometry_hash



class ExploreService:
    """Central domain service orchestrating the Explore data pipeline."""

    def __init__(self):
        self.local_provider = LocalRasterProvider()
        self.stac_provider = STACProvider()
        self._layers: Dict[str, ExploreLayer] = {}
        self._init_default_layers()

    def _init_default_layers(self) -> None:
        """Initializes canonical base and default satellite layers."""
        self._layers["layer-base-dark"] = ExploreLayer(
            id="layer-base-dark",
            name="Dark Canvas Basemap",
            category="base",
            enabled=True,
            user_controllable=True,
            ai_controllable=False,
            default_visible=True,
            renderer_support=["2d", "3d"],
            min_zoom=0,
            max_zoom=20,
            expensive=False,
            opacity=1.0,
            attribution="Esri / OpenStreetMap",
        )
        self._layers["layer-borders"] = ExploreLayer(
            id="layer-borders",
            name="Political Boundaries",
            category="system",
            enabled=True,
            user_controllable=True,
            ai_controllable=True,
            default_visible=False,
            renderer_support=["2d", "3d"],
            min_zoom=2,
            max_zoom=18,
            expensive=False,
            opacity=0.8,
            attribution="Natural Earth / Survey of India",
        )
        self._layers["layer-local_sentinel2_nagpur_truecolor"] = ExploreLayer(
            id="layer-local_sentinel2_nagpur_truecolor",
            name="Sentinel-2 Nagpur True Color",
            category="imagery",
            enabled=True,
            user_controllable=True,
            ai_controllable=True,
            default_visible=False,
            renderer_support=["2d", "3d"],
            min_zoom=4,
            max_zoom=18,
            expensive=False,
            opacity=1.0,
            tile_template="/api/v1/explore/tiles/layer-local_sentinel2_nagpur_truecolor/{z}/{x}/{y}.png",
            attribution="TRINETRA / Sentinel-2 MSI",
            asset_id="local_sentinel2_nagpur_truecolor",
        )
        self._layers["layer-local_sentinel1_mumbai_sar"] = ExploreLayer(
            id="layer-local_sentinel1_mumbai_sar",
            name="Sentinel-1 Mumbai Radar (SAR VV)",
            category="imagery",
            enabled=True,
            user_controllable=True,
            ai_controllable=True,
            default_visible=False,
            renderer_support=["2d", "3d"],
            min_zoom=4,
            max_zoom=18,
            expensive=False,
            opacity=1.0,
            tile_template="/api/v1/explore/tiles/layer-local_sentinel1_mumbai_sar/{z}/{x}/{y}.png",
            attribution="TRINETRA / Sentinel-1 C-SAR",
            asset_id="local_sentinel1_mumbai_sar",
        )

    def get_status(self) -> CatalogStatusResponse:
        """Audits status across all integrated catalog providers and cache metrics."""
        return CatalogStatusResponse(
            local_provider=self.local_provider.status(),
            stac_provider=self.stac_provider.status(),
            stac_endpoint=self.stac_provider.endpoint_url,
            cache="ready",
            indexed_assets=len(self.local_provider._index),
        )

    def search(self, request: ExploreSearchRequest) -> ExploreSearchResponse:
        """Searches local index and/or external STAC catalog with normalized output."""
        items: List[EOItem] = []

        if request.provider in ("all", "local"):
            local_items = self.local_provider.search(request)
            items.extend(local_items)

        if request.provider in ("all", "copernicus") and len(items) < request.limit:
            stac_req = request.model_copy()
            stac_req.limit = request.limit - len(items)
            stac_items = self.stac_provider.search(stac_req)
            items.extend(stac_items)

        # Convert to Pydantic responses
        item_responses: List[EOItemResponse] = []
        for i in items[:request.limit]:
            assets_res = {
                k: EOAssetResponse(
                    id=v.id,
                    href=v.href,
                    media_type=v.media_type,
                    role=v.role,
                    title=v.title,
                    bands=v.bands,
                )
                for k, v in i.assets.items()
            }
            item_responses.append(
                EOItemResponse(
                    id=i.id,
                    collection=i.collection,
                    datetime=i.datetime,
                    bbox=i.bbox,
                    cloud_cover=i.cloud_cover,
                    provider=i.provider,
                    thumbnail_url=i.thumbnail_url,
                    assets=assets_res,
                    properties=i.properties,
                )
            )

        return ExploreSearchResponse(
            items=item_responses,
            total_matched=len(item_responses),
            provider=request.provider or "all",
        )

    def get_item(self, item_id: str) -> Optional[EOItemResponse]:
        item = self.local_provider.get_item(item_id) or self.stac_provider.get_item(item_id)
        if not item:
            return None

        assets_res = {
            k: EOAssetResponse(
                id=v.id,
                href=v.href,
                media_type=v.media_type,
                role=v.role,
                title=v.title,
                bands=v.bands,
            )
            for k, v in item.assets.items()
        }
        return EOItemResponse(
            id=item.id,
            collection=item.collection,
            datetime=item.datetime,
            bbox=item.bbox,
            cloud_cover=item.cloud_cover,
            provider=item.provider,
            thumbnail_url=item.thumbnail_url,
            assets=assets_res,
            properties=item.properties,
        )

    def search_observations(self, request: TemporalSearchRequest) -> TemporalSearchResponse:
        """
        Coordinates multi-temporal acquisition discovery across local fixtures and external STAC,
        enforcing AOI validation, deterministic sorting, and caching.
        """
        start_time = time.time()
        req_id = f"req_{uuid.uuid4().hex[:10]}"

        # Validate AOI if supplied
        if request.aoi:
            val_result = AOIValidator.validate(request.aoi)
            if not val_result.valid:
                raise ValueError(f"Invalid AOI geometry: {'; '.join(val_result.errors)}")

        aoi_h = geometry_hash(request.aoi) if request.aoi else "global"
        cache_key = build_temporal_cache_key(
            aoi_hash=aoi_h,
            start_dt=request.start_datetime,
            end_dt=request.end_datetime,
            collections=request.collections,
            cloud_max=request.cloud_cover_max,
            sort=request.sort,
            limit=request.limit,
        )
        cached = temporal_search_cache.get(cache_key)
        if cached is not None:
            return TemporalSearchResponse(
                request_id=req_id,
                observations=cached,
                total=len(cached),
                has_more=False,
                query=request.model_dump(),
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
                cache_hit=True,
            )

        # 1. Search local provider
        observations: List[ObservationSummary] = self.local_provider.search_temporal(request)

        # 2. Search STAC provider if needed to fulfill request
        if len(observations) < request.limit:
            stac_results = self.stac_provider.search_temporal(request)
            observations.extend(stac_results)

        # 3. Sort & deduplicate
        deduped = TemporalSorter.sort_and_deduplicate(observations, sort_order=request.sort)
        final_obs = deduped[: request.limit]

        temporal_search_cache.set(cache_key, final_obs, ttl_seconds=300.0)

        return TemporalSearchResponse(
            request_id=req_id,
            observations=final_obs,
            total=len(final_obs),
            has_more=len(deduped) > len(final_obs),
            query=request.model_dump(),
            execution_time_ms=round((time.time() - start_time) * 1000, 2),
            cache_hit=False,
        )

    def get_observation(self, observation_id: str) -> Optional[ObservationDetails]:
        """Retrieves detailed metadata for an observation by ID."""
        # 1. Check local indexed items
        item = self.local_provider.get_item(observation_id)
        if item:
            return ObservationNormalizer.to_details(item)

        # 2. Check local assets
        asset = self.local_provider.get_asset(observation_id)
        if asset:
            return ObservationNormalizer.to_details({
                "id": asset.id,
                "collection": "local-raster",
                "datetime": "2026-01-01T00:00:00Z",
                "properties": {"platform": "TRINETRA Local"},
                "assets": {asset.id: {"href": asset.href, "media_type": asset.media_type, "title": asset.title}},
            })

        # 3. Check STAC catalog
        stac_item = self.stac_provider.get_item(observation_id)
        if stac_item:
            return ObservationNormalizer.to_details(stac_item)

        return None



    def get_asset(self, asset_id: str) -> Optional[EOAssetResponse]:
        if not LayerPolicyEngine.validate_safe_asset_id(asset_id):
            return None

        asset = self.local_provider.get_asset(asset_id)
        if not asset:
            return None
        return EOAssetResponse(
            id=asset.id,
            href=asset.href,
            media_type=asset.media_type,
            role=asset.role,
            title=asset.title,
            bands=asset.bands,
        )

    def get_metadata(self, asset_id: str) -> Optional[RasterMetadataResponse]:
        if not LayerPolicyEngine.validate_safe_asset_id(asset_id):
            return None

        local_path = self.local_provider.get_local_path(asset_id)
        if not local_path:
            return None

        source = RasterService.read_metadata(local_path, asset_id)
        return RasterMetadataResponse(
            asset_id=source.asset_id,
            crs=source.crs,
            bounds=source.bounds,
            width=source.width,
            height=source.height,
            bands=source.bands,
            dtype=source.dtype,
            nodata=source.nodata,
            resolution=source.resolution,
            sensor_name=source.sensor_name,
            modality=source.modality,
            is_cog=source.is_cog,
        )

    def list_layers(self) -> List[LayerResponse]:
        """Returns all registered user-visible layers."""
        return [
            LayerResponse(
                id=l.id,
                name=l.name,
                category=l.category,
                enabled=l.enabled,
                user_controllable=l.user_controllable,
                ai_controllable=l.ai_controllable,
                default_visible=l.default_visible,
                renderer_support=l.renderer_support,
                min_zoom=l.min_zoom,
                max_zoom=l.max_zoom,
                expensive=l.expensive,
                opacity=l.opacity,
                tile_template=l.tile_template,
                attribution=l.attribution,
                asset_id=l.asset_id,
            )
            for l in self._layers.values()
        ]

    def get_layer(self, layer_id: str) -> Optional[LayerResponse]:
        l = self._layers.get(layer_id)
        if not l:
            return None
        return LayerResponse(
            id=l.id,
            name=l.name,
            category=l.category,
            enabled=l.enabled,
            user_controllable=l.user_controllable,
            ai_controllable=l.ai_controllable,
            default_visible=l.default_visible,
            renderer_support=l.renderer_support,
            min_zoom=l.min_zoom,
            max_zoom=l.max_zoom,
            expensive=l.expensive,
            opacity=l.opacity,
            tile_template=l.tile_template,
            attribution=l.attribution,
            asset_id=l.asset_id,
        )

    def register_dataset_layer(self, asset_id: str, title: Optional[str] = None) -> Optional[LayerResponse]:
        """Registers a discovered raster dataset as an active imagery layer with tile URL template."""
        if not LayerPolicyEngine.validate_safe_asset_id(asset_id):
            return None

        local_path = self.local_provider.get_local_path(asset_id)
        if not local_path:
            return None

        source = RasterService.read_metadata(local_path, asset_id)
        layer_id = f"layer-{asset_id}"

        layer = ExploreLayer(
            id=layer_id,
            name=title or source.sensor_name or asset_id,
            category="imagery",
            enabled=True,
            user_controllable=True,
            ai_controllable=True,
            default_visible=True,
            renderer_support=["2d", "3d"],
            min_zoom=0,
            max_zoom=20,
            expensive=False,
            opacity=1.0,
            tile_template=f"/api/v1/explore/tiles/{layer_id}/{{z}}/{{x}}/{{y}}.png",
            attribution=f"TRINETRA / {source.sensor_name or 'EO Archive'}",
            asset_id=asset_id,
        )

        self._layers[layer_id] = layer
        return self.get_layer(layer_id)

    def render_tile(self, layer_id: str, z: int, x: int, y: int) -> Optional[bytes]:
        """Coordinates layer lookup, asset resolution, and tile generation."""
        # Find layer
        layer = self._layers.get(layer_id)
        asset_id = layer.asset_id if layer else layer_id.replace("layer-", "")

        if not LayerPolicyEngine.validate_safe_asset_id(asset_id):
            return None

        local_path = self.local_provider.get_local_path(asset_id)
        if not local_path:
            return None

        source = RasterService.read_metadata(local_path, asset_id)
        return TileService.get_tile(layer_id, source, z, x, y)


# Global singleton ExploreService instance
explore_service = ExploreService()
