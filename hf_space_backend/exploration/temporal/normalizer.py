"""
TRINETRA / Shanetra Geospatial Exploration Engine
Observation Normalizer & Bounded Summaries
Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
Normalizes heterogeneous STAC items into compact, stable TRINETRA observation summaries.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ObservationSummary(BaseModel):
    """Compact summary for timeline chips, list views, and comparison selectors."""
    id: str
    collection: str
    datetime: str
    cloud_cover: Optional[float] = None
    platform: Optional[str] = None
    bbox: List[float] = Field(default_factory=list)
    thumbnail: Optional[str] = None
    preview_url: Optional[str] = None
    asset_keys: List[str] = Field(default_factory=list)


class ObservationDetails(ObservationSummary):
    """Detailed observation metadata returned upon user selection."""
    geometry: Optional[Dict[str, Any]] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    assets: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class ObservationNormalizer:
    """Safely extracts normalized observations from raw STAC dictionaries or pystac.Item instances."""

    @classmethod
    def to_summary(cls, item: Any) -> ObservationSummary:
        # Dictionary representation
        if isinstance(item, dict):
            item_id = str(item.get("id", "unknown_observation"))
            collection = str(item.get("collection", "generic-collection"))
            props = item.get("properties", {}) or {}
            dt = props.get("datetime") or item.get("datetime") or "1970-01-01T00:00:00Z"

            cloud = props.get("eo:cloud_cover") or props.get("cloud_cover") or props.get("cloudCover")
            platform = props.get("platform") or props.get("constellation") or "Earth Observation"
            bbox = item.get("bbox") or []

            assets_raw = item.get("assets", {}) or {}
            asset_keys = list(assets_raw.keys())

            # Find thumbnail if present
            thumb = None
            if "thumbnail" in assets_raw and isinstance(assets_raw["thumbnail"], dict):
                thumb = assets_raw["thumbnail"].get("href")
            elif "preview" in assets_raw and isinstance(assets_raw["preview"], dict):
                thumb = assets_raw["preview"].get("href")

            return ObservationSummary(
                id=item_id,
                collection=collection,
                datetime=str(dt),
                cloud_cover=round(float(cloud), 1) if cloud is not None else None,
                platform=str(platform),
                bbox=[float(x) for x in bbox] if bbox else [],
                thumbnail=thumb,
                preview_url=thumb,
                asset_keys=asset_keys,
            )

        # Object representation (EOItem dataclass or PySTAC Item)
        else:
            item_id = getattr(item, "id", "unknown_observation")
            collection = getattr(item, "collection", None) or getattr(item, "collection_id", None) or "generic-collection"
            dt_val = getattr(item, "datetime", None)
            if isinstance(dt_val, str):
                dt = dt_val
            elif hasattr(dt_val, "isoformat"):
                dt = dt_val.isoformat()
            else:
                dt = "1970-01-01T00:00:00Z"

            props = getattr(item, "properties", {}) or {}
            cloud = props.get("eo:cloud_cover") or props.get("cloud_cover") or getattr(item, "cloud_cover", None)
            platform = props.get("platform") or getattr(item, "provider", "Earth Observation")
            bbox = getattr(item, "bbox", [])

            assets_map = getattr(item, "assets", {}) or {}
            asset_keys = list(assets_map.keys())

            thumb = getattr(item, "thumbnail_url", None)
            if not thumb and "thumbnail" in assets_map:
                t_val = assets_map["thumbnail"]
                thumb = t_val.get("href") if isinstance(t_val, dict) else getattr(t_val, "href", None)

            return ObservationSummary(
                id=item_id,
                collection=collection,
                datetime=str(dt),
                cloud_cover=round(float(cloud), 1) if cloud is not None else None,
                platform=str(platform),
                bbox=[float(x) for x in bbox] if bbox else [],
                thumbnail=thumb,
                preview_url=thumb,
                asset_keys=asset_keys,
            )

    @classmethod
    def to_details(cls, item: Any) -> ObservationDetails:
        summary = cls.to_summary(item)
        if isinstance(item, dict):
            geom = item.get("geometry")
            props = item.get("properties", {}) or {}
            assets = item.get("assets", {}) or {}
        else:
            geom = getattr(item, "geometry", None)
            props = getattr(item, "properties", {}) or {}
            assets_raw = getattr(item, "assets", {}) or {}
            assets = {}
            for k, v in assets_raw.items():
                if isinstance(v, dict):
                    assets[k] = v
                else:
                    assets[k] = {
                        "href": getattr(v, "href", ""),
                        "media_type": getattr(v, "media_type", ""),
                        "title": getattr(v, "title", k),
                    }

        return ObservationDetails(
            **summary.model_dump(),
            geometry=geom,
            properties=props,
            assets=assets,
        )

