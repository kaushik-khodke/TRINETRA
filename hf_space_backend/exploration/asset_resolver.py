"""
TRINETRA / Shanetra Geospatial Exploration Engine
Asset Resolver Service
Phase 2: Translates EOItems and logical asset IDs into validated raster sources without downloading whole products.
"""

from typing import Optional, Dict, Any
from exploration.models import EOItem, EOAsset, RasterSource
from exploration.policies import LayerPolicyEngine
from exploration.raster_service import RasterService


class AssetResolver:
    """Resolves EO observation items and logical asset IDs into streamable raster descriptors."""

    @staticmethod
    def resolve_visual_asset(item: EOItem) -> Optional[EOAsset]:
        """Finds the most appropriate visual rendering asset from an EOItem."""
        if not item.assets:
            return None

        # Priority 1: explicitly marked 'visual' or 'true_color'
        for asset in item.assets.values():
            if asset.role in ("visual", "true_color", "tci"):
                return asset

        # Priority 2: RGB composite or B04/B03/B02
        for asset in item.assets.values():
            if "visual" in asset.id.lower() or "tci" in asset.id.lower():
                return asset

        # Priority 3: SAR backscatter
        for asset in item.assets.values():
            if asset.role in ("sar", "intensity", "vv", "vh"):
                return asset

        # Fallback: return first raster asset
        for asset in item.assets.values():
            if "image" in asset.media_type:
                return asset

        return None

    @classmethod
    def resolve_raster_source(cls, asset: EOAsset) -> Optional[RasterSource]:
        """Translates an EOAsset with a verified local path into an authoritative RasterSource."""
        if not asset.local_path:
            return None

        if not LayerPolicyEngine.validate_safe_asset_id(asset.id):
            return None

        return RasterService.read_metadata(asset.local_path, asset.id)
