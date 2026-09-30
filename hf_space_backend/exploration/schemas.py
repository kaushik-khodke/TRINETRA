"""
TRINETRA / Shanetra Geospatial Exploration Engine
FastAPI Request & Response Schemas (Pydantic V2)
Phase 2: Strict validation, bounded responses, zero internal path exposure.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator


class ExploreSearchRequest(BaseModel):
    """Search request with bounded parameters for EO observation discovery."""
    bbox: Optional[List[float]] = Field(
        default=None,
        description="Bounding box in EPSG:4326 [min_lon, min_lat, max_lon, max_lat]",
        min_length=4,
        max_length=4,
    )
    datetime_start: Optional[str] = Field(default=None, description="ISO-8601 start timestamp")
    datetime_end: Optional[str] = Field(default=None, description="ISO-8601 end timestamp")
    collections: Optional[List[str]] = Field(default=None, description="EO collections to search")
    cloud_cover_max: Optional[float] = Field(default=100.0, ge=0.0, le=100.0, description="Max cloud percentage")
    provider: Optional[str] = Field(default="all", description="Provider filter: 'all', 'local', or 'copernicus'")
    limit: int = Field(default=10, ge=1, le=50, description="Hard-bounded maximum results per query")

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, v: Optional[List[float]]) -> Optional[List[float]]:
        if v is not None:
            min_lon, min_lat, max_lon, max_lat = v
            if not (-180.0 <= min_lon <= 180.0 and -180.0 <= max_lon <= 180.0):
                raise ValueError("Longitude must be between -180.0 and 180.0 degrees")
            if not (-90.0 <= min_lat <= 90.0 and -90.0 <= max_lat <= 90.0):
                raise ValueError("Latitude must be between -90.0 and 90.0 degrees")
            if min_lon > max_lon:
                raise ValueError("min_lon cannot exceed max_lon")
            if min_lat > max_lat:
                raise ValueError("min_lat cannot exceed max_lat")
        return v


class EOAssetResponse(BaseModel):
    id: str
    href: str
    media_type: str
    role: str
    title: Optional[str] = None
    bands: Optional[List[str]] = None


class EOItemResponse(BaseModel):
    id: str
    collection: str
    datetime: str
    bbox: List[float]
    cloud_cover: Optional[float] = None
    provider: str
    thumbnail_url: Optional[str] = None
    assets: Dict[str, EOAssetResponse] = Field(default_factory=dict)
    properties: Dict[str, Any] = Field(default_factory=dict)


class ExploreSearchResponse(BaseModel):
    items: List[EOItemResponse]
    total_matched: int
    provider: str


class LayerResponse(BaseModel):
    id: str
    name: str
    category: str
    enabled: bool
    user_controllable: bool
    ai_controllable: bool
    default_visible: bool
    renderer_support: List[str]
    min_zoom: int
    max_zoom: int
    expensive: bool
    opacity: float
    tile_template: Optional[str] = None
    attribution: Optional[str] = None
    asset_id: Optional[str] = None


class RasterMetadataResponse(BaseModel):
    asset_id: str
    crs: str
    bounds: List[float]
    width: int
    height: int
    bands: int
    dtype: str
    nodata: Optional[float] = None
    resolution: Optional[List[float]] = None
    sensor_name: Optional[str] = None
    modality: str
    is_cog: bool


class TileSourceResponse(BaseModel):
    layer_id: str
    tile_url_template: str
    min_zoom: int
    max_zoom: int
    bounds: Optional[List[float]] = None
    tile_size: int
    format: str


class CatalogStatusResponse(BaseModel):
    local_provider: str
    stac_provider: str
    stac_endpoint: str
    cache: str
    indexed_assets: int


class ExploreErrorResponse(BaseModel):
    error_code: str
    message: str
    retryable: bool = False
