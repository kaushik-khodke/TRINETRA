"""
TRINETRA / Shanetra Geospatial Exploration Engine
FastAPI Explore Router
Phase 2: Exposes REST endpoints for EO discovery, metadata inspection, layer registry, and tile streaming.
"""

import hashlib
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Response, Path
from fastapi.responses import JSONResponse

from exploration.schemas import (
    ExploreSearchRequest,
    ExploreSearchResponse,
    EOItemResponse,
    EOAssetResponse,
    LayerResponse,
    RasterMetadataResponse,
    CatalogStatusResponse,
)
from exploration.ai_schemas import (
    ExploreAIQueryRequest,
    ExploreAIQueryResponse,
    ExploreAIStatusResponse,
)
from exploration.aoi.validator import AOIValidator, AOIValidationResult
from exploration.temporal.normalizer import ObservationDetails
from exploration.temporal.search import TemporalSearchRequest, TemporalSearchResponse
from exploration.comparison.models import ComparisonValidationRequest, ComparisonValidationResponse
from exploration.comparison.service import comparison_service
from exploration.service import explore_service
from exploration.ai_service import explore_ai_service
from exploration.policies import LayerPolicyEngine

router = APIRouter(prefix="/api/v1/explore", tags=["explore"])



@router.get("/catalog/status", response_model=CatalogStatusResponse)
def get_catalog_status():
    """Returns the operational status of local raster index, STAC catalog, and caching."""
    return explore_service.get_status()


@router.post("/search", response_model=ExploreSearchResponse)
def search_catalog(request: ExploreSearchRequest):
    """Searches indexed local and external STAC Earth Observation observations."""
    return explore_service.search(request)


@router.get("/items/{item_id}", response_model=EOItemResponse)
def get_item(item_id: str = Path(..., description="Unique EO observation item ID")):
    """Retrieves full metadata for an individual satellite observation."""
    item = explore_service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"EO Item '{item_id}' not found.")
    return item


@router.get("/assets/{asset_id}", response_model=EOAssetResponse)
def get_asset(asset_id: str = Path(..., description="Safe asset ID")):
    """Inspects metadata of a specific raster asset without triggering file download."""
    if not LayerPolicyEngine.validate_safe_asset_id(asset_id):
        raise HTTPException(status_code=400, detail="Invalid asset ID format or path traversal attempt.")
    asset = explore_service.get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail=f"Asset '{asset_id}' not found.")
    return asset


@router.get("/metadata/{asset_id}", response_model=RasterMetadataResponse)
def get_raster_metadata(asset_id: str = Path(..., description="Safe asset ID")):
    """Inspects authoritative raster dimensions, bounds, CRS, and bands directly from headers."""
    if not LayerPolicyEngine.validate_safe_asset_id(asset_id):
        raise HTTPException(status_code=400, detail="Invalid asset ID format.")
    meta = explore_service.get_metadata(asset_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Raster metadata for '{asset_id}' not found.")
    return meta


@router.get("/layers", response_model=List[LayerResponse])
def list_layers():
    """Lists all active and available user-visible layers."""
    return explore_service.list_layers()


@router.get("/layers/{layer_id}", response_model=LayerResponse)
def get_layer(layer_id: str = Path(...)):
    """Retrieves layer configuration and tile template."""
    layer = explore_service.get_layer(layer_id)
    if not layer:
        raise HTTPException(status_code=404, detail=f"Layer '{layer_id}' not found.")
    return layer


@router.post("/layers/register", response_model=LayerResponse)
def register_dataset_layer(
    asset_id: str = Query(..., description="Asset ID to promote to a tile layer"),
    title: Optional[str] = Query(None, description="Optional custom title for the layer"),
):
    """Registers a discovered raster dataset as a live tileable imagery layer."""
    if not LayerPolicyEngine.validate_safe_asset_id(asset_id):
        raise HTTPException(status_code=400, detail="Invalid asset ID format.")
    layer = explore_service.register_dataset_layer(asset_id, title)
    if not layer:
        raise HTTPException(status_code=404, detail=f"Raster asset '{asset_id}' could not be registered.")
    return layer


@router.get("/tiles/{layer_id}/{z}/{x}/{y}.png")
def get_tile(
    layer_id: str = Path(..., description="Layer or asset ID"),
    z: int = Path(..., ge=0, le=22, description="Zoom level"),
    x: int = Path(..., ge=0, description="Tile X coordinate"),
    y: int = Path(..., ge=0, description="Tile Y coordinate"),
):
    """
    Renders or serves a 256x256 PNG raster tile.
    Supports HTTP 304 Not Modified, ETag, and Cache-Control headers.
    """
    # 1. Reject invalid tile bounds
    max_coord = (1 << z) - 1
    if x > max_coord or y > max_coord:
        raise HTTPException(status_code=400, detail=f"Tile coordinate ({x}, {y}) out of range for zoom {z}.")

    # 2. Render tile via ExploreService
    tile_bytes = explore_service.render_tile(layer_id, z, x, y)
    if not tile_bytes:
        raise HTTPException(status_code=404, detail=f"Tile ({z}/{x}/{y}) not available for layer '{layer_id}'.")

    # 3. Generate deterministic ETag
    etag = f'"{hashlib.md5(tile_bytes).hexdigest()}"'

    headers = {
        "Content-Type": "image/png",
        "Cache-Control": "public, max-age=900, must-revalidate",
        "ETag": etag,
        "X-Shanetra-Layer": layer_id,
    }

    return Response(content=tile_bytes, media_type="image/png", headers=headers)


# --- Phase 3: AI Natural-Language Exploration Gateway ---

@router.get("/ai/status", response_model=ExploreAIStatusResponse)
def get_ai_status():
    """Returns local LLM availability, active models, and structured generation status."""
    return explore_ai_service.get_status()


@router.post("/ai/query", response_model=ExploreAIQueryResponse)
def query_explore_ai(request: ExploreAIQueryRequest):
    """
    Interprets natural-language Earth exploration commands and returns a validated,
    structured execution patch without permitting direct LLM renderer access.
    """
    return explore_ai_service.process_query(request)


# --- Phase 4: Temporal Exploration, AOI & Observation Comparison ---

@router.post("/aoi/validate", response_model=AOIValidationResult)
def validate_aoi(payload: Dict[str, Any]):
    """
    Validates an AOI geometry or Feature against server-authoritative AOIPolicy:
    checks vertex count, area (<= 250,000 km2), closed polygon rings, and self-intersections.
    """
    geojson = payload.get("aoi", payload)
    return AOIValidator.validate(geojson)


@router.post("/observations/search", response_model=TemporalSearchResponse)
def search_observations(request: TemporalSearchRequest):
    """
    Discovers multi-temporal acquisitions for an AOI and datetime range,
    filtered by cloud cover and sorted deterministically.
    """
    try:
        return explore_service.search_observations(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Observation search error: {e}")


@router.get("/observations/{observation_id}", response_model=ObservationDetails)
def get_observation_details(observation_id: str = Path(..., description="Unique observation ID")):
    """Retrieves full metadata, geometry, and asset endpoints for an observation."""
    obs = explore_service.get_observation(observation_id)
    if not obs:
        raise HTTPException(status_code=404, detail=f"Observation '{observation_id}' not found.")
    return obs


@router.post("/comparison/validate", response_model=ComparisonValidationResponse)
def validate_comparison(request: ComparisonValidationRequest):
    """
    Validates compatibility of two observations (spatial overlap >= 10%, temporal delta, different IDs)
    for dual-observation comparison modes.
    """
    return comparison_service.validate_comparison(request)


