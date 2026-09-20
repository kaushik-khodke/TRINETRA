"""
TRINETRA / Shanetra Geospatial Exploration Engine
Internal Data Structures (Domain Models)
Phase 2: Independent internal representations isolated from external APIs and frontend models.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple


@dataclass
class EOAsset:
    """Represents an individual raster or metadata file within an EO observation."""
    id: str
    href: str
    media_type: str = "image/tiff; application=geotiff"
    role: str = "visual"  # visual, red, green, blue, nir, sar, thumbnail, metadata
    title: Optional[str] = None
    bands: Optional[List[str]] = None
    local_path: Optional[str] = None
    is_cog: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EOItem:
    """Represents a discrete Earth Observation observation with provenance."""
    id: str
    collection: str
    datetime: str
    bbox: List[float]  # [min_lon, min_lat, max_lon, max_lat] in EPSG:4326
    geometry: Optional[Dict[str, Any]] = None
    cloud_cover: Optional[float] = None
    assets: Dict[str, EOAsset] = field(default_factory=dict)
    provider: str = "local"  # "local", "copernicus", "isro"
    thumbnail_url: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    source_url: Optional[str] = None
    ingestion_time: Optional[str] = None


@dataclass
class EOCollection:
    """Represents an EO dataset catalog collection (e.g. sentinel-2-l2a)."""
    id: str
    title: str
    description: str
    provider: str
    spatial_extent: Optional[List[float]] = None
    temporal_extent: Optional[List[str]] = None


@dataclass
class RasterSource:
    """Describes an authoritative georeferenced raster file ready for windowed reads."""
    asset_id: str
    path: str
    crs: str
    bounds: List[float]  # [min_lon, min_lat, max_lon, max_lat] in EPSG:4326
    width: int
    height: int
    bands: int
    dtype: str
    nodata: Optional[float] = None
    resolution: Optional[List[float]] = None
    transform_matrix: Optional[List[float]] = None
    is_cog: bool = False
    sensor_name: Optional[str] = None
    modality: str = "optical"


@dataclass
class TileSource:
    """Metadata contract describing a slippy tile source for MapLibre/Cesium."""
    layer_id: str
    tile_url_template: str
    min_zoom: int = 0
    max_zoom: int = 20
    bounds: Optional[List[float]] = None
    tile_size: int = 256
    format: str = "png"


@dataclass
class ExploreLayer:
    """Governed user-visible or system layer definition."""
    id: str
    name: str
    category: str  # "base", "imagery", "analytical", "system"
    enabled: bool = True
    user_controllable: bool = True
    ai_controllable: bool = True
    default_visible: bool = False
    renderer_support: List[str] = field(default_factory=lambda: ["2d", "3d"])
    min_zoom: int = 0
    max_zoom: int = 20
    expensive: bool = False
    opacity: float = 1.0
    tile_template: Optional[str] = None
    attribution: Optional[str] = None
    asset_id: Optional[str] = None
