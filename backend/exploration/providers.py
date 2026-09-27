"""
TRINETRA / Shanetra Geospatial Exploration Engine
EO Data Provider Protocol Definition
Phase 2: Abstract contract ensuring frontend and exploration services remain agnostic to data sources.
"""

from dataclasses import dataclass
from typing import Protocol, List, Optional, Dict, Any, runtime_checkable
from exploration.models import EOItem, EOAsset
from exploration.schemas import ExploreSearchRequest


@dataclass
class ProviderCapabilities:
    """Operational capability flags for a STAC or catalog provider."""
    supports_intersects: bool = True
    supports_bbox: bool = True
    supports_datetime: bool = True
    supports_cql2: bool = False
    supports_query: bool = True
    supports_sort: bool = True
    supports_fields: bool = True
    supports_thumbnails: bool = True
    supports_asset_urls: bool = True


@runtime_checkable
class EODataProvider(Protocol):
    """Canonical contract for Earth Observation catalog & data providers."""

    @property
    def provider_name(self) -> str:
        """Normalized unique identifier for the provider (e.g. 'local', 'copernicus')."""
        ...

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Declared query and metadata capabilities of this provider."""
        ...

    def status(self) -> str:
        """Health/availability status ('ready', 'available', 'degraded', 'offline')."""
        ...

    def search(self, request: ExploreSearchRequest) -> List[EOItem]:
        """Searches observation items matching spatial, temporal, and sensor filters."""
        ...

    def get_item(self, item_id: str) -> Optional[EOItem]:
        """Retrieves a single EO observation item by unique ID."""
        ...

    def get_asset(self, asset_id: str) -> Optional[EOAsset]:
        """Retrieves metadata/descriptor for an asset by its unique asset ID."""
        ...

    def get_metadata(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Returns normalized geospatial metadata for an asset."""
        ...
