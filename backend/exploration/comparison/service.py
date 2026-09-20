"""
TRINETRA / Shanetra Geospatial Exploration Engine
Comparison Service & Coordinator
Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
Orchestrates observation resolution, compatibility validation, and layer preparation.
"""

from typing import Optional, Tuple
from exploration.comparison.models import (
    ComparisonMode,
    ComparisonValidationRequest,
    ComparisonValidationResponse,
)
from exploration.comparison.validator import ComparisonValidator
from exploration.temporal.normalizer import ObservationSummary, ObservationNormalizer
from exploration.service import explore_service


class ComparisonService:
    """Orchestrates multi-temporal observation comparison workflows."""

    @classmethod
    def validate_comparison(
        cls, request: ComparisonValidationRequest
    ) -> ComparisonValidationResponse:
        obs_a = cls._resolve_observation_summary(request.observation_a_id)
        obs_b = cls._resolve_observation_summary(request.observation_b_id)
        return ComparisonValidator.validate(obs_a, obs_b, request.mode)

    @classmethod
    def _resolve_observation_summary(cls, observation_id: str) -> Optional[ObservationSummary]:
        """Resolves observation ID from local service or STAC provider."""
        # 1. Check local indexed items
        item = explore_service.get_item(observation_id)
        if item:
            return ObservationSummary(
                id=item.id,
                collection=item.collection,
                datetime=item.datetime,
                cloud_cover=item.cloud_cover,
                platform=item.properties.get("platform", "Earth Observation"),
                bbox=item.bbox or [],
                thumbnail=item.thumbnail_url,
                preview_url=item.thumbnail_url,
                asset_keys=list(item.assets.keys()),
            )

        # 2. Check registered layers or assets
        asset = explore_service.get_asset(observation_id)
        if asset:
            meta = explore_service.get_metadata(observation_id)
            return ObservationSummary(
                id=asset.id,
                collection="local-raster",
                datetime="2026-01-01T00:00:00Z",
                cloud_cover=0.0,
                platform="TRINETRA Local",
                bbox=meta.bounds if meta else [],
                thumbnail=None,
                preview_url=None,
                asset_keys=[asset.id],
            )


        # 3. Fallback: Check STAC catalog
        stac_res = explore_service.stac_provider.get_item(observation_id)
        if stac_res:
            return ObservationNormalizer.to_summary(stac_res)

        return None


# Singleton instance
comparison_service = ComparisonService()
