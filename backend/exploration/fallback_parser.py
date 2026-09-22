"""
TRINETRA / Shanetra Geospatial Exploration Engine
Deterministic Fallback Parser & Fast-Path Router
Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
Sub-millisecond keyword and regex matcher for unambiguous map commands.
Bypasses LLM inference completely for simple commands (reset, zoom, show/hide layers).
"""

import re
from typing import Optional, List
from exploration.ai_schemas import (
    ExploreCommandPlan,
    ExploreCommand,
    ResetViewCommand,
    ZoomInCommand,
    ZoomOutCommand,
    ShowLayerCommand,
    HideLayerCommand,
)

# Canonical layer aliases mapping natural phrases to authoritative registered IDs
LAYER_ALIASES = {
    # Boundaries / borders
    "boundary": "layer-borders",
    "boundaries": "layer-borders",
    "border": "layer-borders",
    "borders": "layer-borders",
    "political boundaries": "layer-borders",
    # Sentinel-2 optical imagery
    "sentinel 2": "layer-sentinel2-cloudless",
    "sentinel-2": "layer-sentinel2-cloudless",
    "s2": "layer-sentinel2-cloudless",
    "optical": "layer-sentinel2-cloudless",
    "optical satellite": "layer-sentinel2-cloudless",
    "satellite layer": "layer-sentinel2-cloudless",
    # Sentinel-1 SAR imagery
    "sentinel 1": "layer-sentinel1-radar",
    "sentinel-1": "layer-sentinel1-radar",
    "s1": "layer-sentinel1-radar",
    "sar": "layer-sentinel1-radar",
    "radar": "layer-sentinel1-radar",
    # NASA VIIRS
    "viirs": "layer-nasa-viirs",
    "nasa": "layer-nasa-viirs",
    # OSM
    "osm": "layer-osm",
    "street": "layer-osm",
}

RESET_REGEX = re.compile(
    r"^(?:reset|reset\s+(?:the\s+)?(?:globe|view|map|camera)|home|recenter|center\s+(?:globe|map))$",
    re.IGNORECASE,
)
ZOOM_IN_REGEX = re.compile(
    r"^(?:zoom\s+in|closer|magnify|enlarge)$",
    re.IGNORECASE,
)
ZOOM_OUT_REGEX = re.compile(
    r"^(?:zoom\s+out|wider|pull\s+back|zoom\s+back)$",
    re.IGNORECASE,
)
SHOW_LAYER_REGEX = re.compile(
    r"^(?:show|enable|turn\s+on|display|activate|add)\s+(?:the\s+)?([a-z0-9\s\-]+?)(?:\s+imagery|\s+layer)?$",
    re.IGNORECASE,
)
HIDE_LAYER_REGEX = re.compile(
    r"^(?:hide|disable|turn\s+off|remove|conceal|deactivate)\s+(?:the\s+)?([a-z0-9\s\-]+?)(?:\s+imagery|\s+layer)?$",
    re.IGNORECASE,
)


CLEAR_AOI_REGEX = re.compile(
    r"^(?:clear|remove|delete|reset)\s+(?:the\s+)?(?:aoi|boundary|selection|polygon|box)$",
    re.IGNORECASE,
)
NAV_REGEX = re.compile(
    r"^(?:focus\s+(?:on|in)?|fly\s+to|go\s+to|zoom\s+to|navigate\s+to|look\s+at|show\s+me|find|center\s+(?:on)?|let(?:'s)?\s+(?:get|go)\s+to|take\s+me\s+to|bring\s+me\s+to|head\s+to|travel\s+to|visit|draw\s+(?:boundaries?|box|square|aoi|region)\s+(?:around|of|for|in)?|show\s+(?:boundaries?|box|square|aoi|region)\s+(?:around|of|for|in)?|highlight)\s+(.+)$",
    re.IGNORECASE,
)


class FallbackParser:
    """Instantaneous deterministic parser for predictable commands."""

    @classmethod
    def parse(cls, query: str) -> Optional[ExploreCommandPlan]:
        """
        Parses a query into an ExploreCommandPlan without calling any LLM.
        Returns None if query cannot be deterministically resolved.
        """
        if not query or not isinstance(query, str):
            return None

        clean = query.strip().lower()
        if not clean:
            return None

        # Defer compound multi-clause or complex dataset search queries to the AI planner
        is_compound = any(
            conj in clean for conj in [" and ", " then ", " with ", " also ", " but "]
        ) or any(
            kw in clean for kw in ["imagery", "observation", "transparent", "opacity", "where is", "find satellite", "cloud cover"]
        )
        if is_compound:
            return None

        # 1. Reset View
        if RESET_REGEX.match(clean):
            return ExploreCommandPlan(
                intent="reset",
                summary="Reset TRINETRA globe to default perspective.",
                commands=[ResetViewCommand()],
            )

        # 2. Clear AOI
        if CLEAR_AOI_REGEX.match(clean):
            from exploration.ai_schemas import ClearAOICommand
            return ExploreCommandPlan(
                intent="aoi_selection",
                summary="Cleared active Area of Interest.",
                commands=[ClearAOICommand()],
            )

        # 3. Zoom In
        if ZOOM_IN_REGEX.match(clean):
            return ExploreCommandPlan(
                intent="view_control",
                summary="Zoomed into the active viewport.",
                commands=[ZoomInCommand(step=1.0)],
            )

        # 4. Zoom Out
        if ZOOM_OUT_REGEX.match(clean):
            return ExploreCommandPlan(
                intent="view_control",
                summary="Zoomed out to a wider perspective.",
                commands=[ZoomOutCommand(step=1.0)],
            )

        # 5. Direct Coordinate Entry ("28.6139, 77.2090" or "lat: 28.61, lon: 77.20")
        from exploration.geo_resolver import DeterministicCoordinateParser, GeoResolver
        coord_target = DeterministicCoordinateParser.parse(clean)
        if coord_target:
            from exploration.ai_schemas import FlyToCommand, SetAOICommand
            bbox = [coord_target.longitude - 0.08, coord_target.latitude - 0.06, coord_target.longitude + 0.08, coord_target.latitude + 0.06]
            return ExploreCommandPlan(
                intent="navigation",
                summary=f"Navigated to coordinates {coord_target.name} and highlighted region.",
                commands=[
                    FlyToCommand(
                        location_query=coord_target.name,
                        latitude=coord_target.latitude,
                        longitude=coord_target.longitude,
                        zoom=12.0,
                        pitch=-50.0,
                    ),
                    SetAOICommand(bbox=bbox),
                ],
            )

        # 6. Navigation Command ("Focus on New Delhi", "Fly to Mumbai", "Go to Bangalore", "Go to delhi")
        nav_match = NAV_REGEX.match(clean)
        target_loc_name = nav_match.group(1).strip() if nav_match else None
        if target_loc_name:
            geo_target = GeoResolver.resolve(target_loc_name)
            if geo_target:
                from exploration.ai_schemas import FlyToCommand, SetAOICommand
                bbox = geo_target.bbox or [geo_target.longitude - 0.08, geo_target.latitude - 0.06, geo_target.longitude + 0.08, geo_target.latitude + 0.06]
                return ExploreCommandPlan(
                    intent="navigation",
                    summary=f"Navigating to {geo_target.name} and highlighting region.",
                    commands=[
                        FlyToCommand(
                            location_query=geo_target.name,
                            latitude=geo_target.latitude,
                            longitude=geo_target.longitude,
                            zoom=11.5,
                            pitch=-50.0,
                        ),
                        SetAOICommand(bbox=bbox),
                    ],
                )

        # 7. Direct City / Location Name ("New Delhi", "Mumbai", "Sriharikota", "Delhi")
        direct_geo = GeoResolver.resolve(clean)
        if direct_geo and direct_geo.confidence >= 0.9:
            from exploration.ai_schemas import FlyToCommand, SetAOICommand
            bbox = direct_geo.bbox or [direct_geo.longitude - 0.08, direct_geo.latitude - 0.06, direct_geo.longitude + 0.08, direct_geo.latitude + 0.06]
            return ExploreCommandPlan(
                intent="navigation",
                summary=f"Navigating to {direct_geo.name} and highlighting region.",
                commands=[
                    FlyToCommand(
                        location_query=direct_geo.name,
                        latitude=direct_geo.latitude,
                        longitude=direct_geo.longitude,
                        zoom=11.5,
                        pitch=-50.0,
                    ),
                    SetAOICommand(bbox=bbox),
                ],
            )

        # 8. Show Layer
        show_match = SHOW_LAYER_REGEX.match(clean)
        if show_match:
            raw_target = show_match.group(1).strip()
            layer_id = cls.resolve_layer_id(raw_target)
            if layer_id:
                return ExploreCommandPlan(
                    intent="layer_control",
                    summary=f"Enabled '{raw_target}' layer.",
                    commands=[ShowLayerCommand(layer_id=layer_id)],
                )

        # 9. Hide Layer
        hide_match = HIDE_LAYER_REGEX.match(clean)
        if hide_match:
            raw_target = hide_match.group(1).strip()
            layer_id = cls.resolve_layer_id(raw_target)
            if layer_id:
                return ExploreCommandPlan(
                    intent="layer_control",
                    summary=f"Hidden '{raw_target}' layer.",
                    commands=[HideLayerCommand(layer_id=layer_id)],
                )

        return None

    @classmethod
    def resolve_layer_id(cls, raw_name: str) -> Optional[str]:
        """Resolves natural language name or alias to registered layer ID."""
        cleaned = raw_name.lower().strip()
        # Direct lookup
        if cleaned in LAYER_ALIASES:
            return LAYER_ALIASES[cleaned]

        # Suffix/prefix stripping (e.g. "boundaries layer" -> "boundaries")
        for alias, layer_id in LAYER_ALIASES.items():
            if alias == cleaned or cleaned.startswith(alias) or cleaned.endswith(alias):
                return layer_id

        # If already starts with layer-
        if cleaned.startswith("layer-"):
            return cleaned

        return None
