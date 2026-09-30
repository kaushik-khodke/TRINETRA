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
    r"^(?:where\s+is(?:\s+the)?|locate(?:\s+the)?|focus\s+(?:on|in)?|fly\s+to|go\s+to|zoom\s+to|navigate\s+to|look\s+at|show\s+me|find(?:\s+the)?|center\s+(?:on)?|let(?:'s)?\s+(?:get|go)\s+to|take\s+me\s+to|bring\s+me\s+to|head\s+to|travel\s+to|visit|draw\s+(?:boundaries|boundary|box|square|aoi|region)\s+(?:around|of|for|in)?|show\s+(?:boundaries|boundary|box|square|aoi|region)\s+(?:around|of|for|in)?|highlight)\s+(.+)$",
    re.IGNORECASE,
)

# Authoritative Earth geographic extremes and superlative knowledge mappings
GEOGRAPHIC_SUPERLATIVES = {
    "pollut": {
        "name": "Lahore, Pakistan",
        "description": "globally ranked #1 on real-time Air Quality Index (AQI) with severe PM2.5 pollution levels",
        "lat": 31.5497,
        "lon": 74.3436,
        "bbox": [74.20, 31.40, 74.45, 31.65],
        "zoom": 11.5,
    },
    "hottest": {
        "name": "Death Valley (Furnace Creek), California, USA",
        "description": "Earth's highest reliably measured air temperature at 56.7°C (134°F)",
        "lat": 36.4623,
        "lon": -116.8669,
        "bbox": [-117.15, 36.30, -116.60, 36.70],
        "zoom": 10.5,
    },
    "coldest": {
        "name": "Oymyakon, Sakha Republic, Russia",
        "description": "the coldest permanently inhabited settlement on Earth (-67.7°C / -89.9°F)",
        "lat": 63.4641,
        "lon": 142.7728,
        "bbox": [142.60, 63.35, 142.95, 63.55],
        "zoom": 11.5,
    },
    "highest": {
        "name": "Mount Everest, Himalayas",
        "description": "highest elevation peak above sea level on Earth (8,848.86 m)",
        "lat": 27.9881,
        "lon": 86.9250,
        "bbox": [86.90, 27.96, 86.95, 28.01],
        "zoom": 13.0,
    },
    "deepest": {
        "name": "Mariana Trench (Challenger Deep), Pacific Ocean",
        "description": "deepest oceanic trench on Earth (-10,928 m)",
        "lat": 11.3733,
        "lon": 142.5917,
        "bbox": [142.40, 11.20, 142.80, 11.55],
        "zoom": 9.0,
    },
    "wettest": {
        "name": "Mawsynram, Meghalaya, India",
        "description": "highest average annual precipitation on Earth (~11,872 mm)",
        "lat": 25.2975,
        "lon": 91.5826,
        "bbox": [91.50, 25.20, 91.65, 25.38],
        "zoom": 12.0,
    },
    "driest": {
        "name": "Atacama Desert, Chile",
        "description": "driest non-polar desert on Earth",
        "lat": -23.8634,
        "lon": -69.1328,
        "bbox": [-70.50, -25.50, -68.00, -22.00],
        "zoom": 7.5,
    },
}


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
            conj in clean for conj in [" and ", " then ", " with ", " also ", " but ", " near ", " next to ", " between "]
        ) or any(
            kw in clean for kw in ["imagery", "observation", "transparent", "opacity", "find satellite", "cloud cover"]
        )
        if is_compound:
            return None

        # Defer semantic questions, country capitals, superlatives, and knowledge queries to the LLM
        is_knowledge_query = (
            clean.endswith("?")
            or any(clean.startswith(prefix) for prefix in [
                "what", "where", "which", "who", "when", "why", "how",
                "tell me", "explain", "describe", "find me", "can you",
                "capital of", "capital",
            ])
            or "capital of" in clean
            or any(w in clean for w in [
                "largest", "smallest", "biggest", "highest", "deepest",
                "hottest", "coldest", "richest", "poorest", "population of",
            ])
        )
        if is_knowledge_query:
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

        # 6. Show Layer ("show boundaries", "turn on s2", "enable radar")
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

        # 7. Hide Layer ("hide boundaries", "turn off radar")
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

        # 8. Navigation Command ("Focus on New Delhi", "Fly to Mumbai", "Go to Bangalore", "Go to delhi", "Go to China", "Go to alaska", "go to the most polluted city")
        nav_match = NAV_REGEX.match(clean)
        target_loc_name = nav_match.group(1).strip() if nav_match else None
        if target_loc_name:
            target_lower = target_loc_name.lower()

            # If user said "Where is the capital of X" or similar, defer to LLM reasoning
            if any(target_lower.startswith(p) for p in ["the capital", "capital", "what", "where"]) or "capital of" in target_lower:
                return None

            # Check geographic superlatives knowledge first (e.g. "most polluted city", "hottest place")
            for key, sup_entry in GEOGRAPHIC_SUPERLATIVES.items():
                if key in target_lower or key in clean:
                    from exploration.ai_schemas import FlyToCommand, SetAOICommand
                    return ExploreCommandPlan(
                        intent="navigation",
                        summary=f"Navigated to {sup_entry['name']} ({sup_entry['description']}) and highlighted region.",
                        commands=[
                            FlyToCommand(
                                location_query=sup_entry["name"],
                                latitude=sup_entry["lat"],
                                longitude=sup_entry["lon"],
                                zoom=sup_entry["zoom"],
                                pitch=-50.0,
                            ),
                            SetAOICommand(bbox=sup_entry["bbox"]),
                        ],
                    )

            # Prevent dynamic ranking/superlative phrases from fuzzy-matching random street/bridge names in literal geocoder
            if re.search(r"\b(most|least|best|worst|richest|poorest)\b", target_lower):
                return None

            geo_target = GeoResolver.resolve(target_loc_name, allow_online=True)
            if geo_target:
                from exploration.ai_schemas import FlyToCommand, SetAOICommand
                bbox = geo_target.bbox or [geo_target.longitude - 0.08, geo_target.latitude - 0.06, geo_target.longitude + 0.08, geo_target.latitude + 0.06]
                zoom = geo_target.zoom or cls.calculate_zoom(bbox)
                pitch = -35.0 if zoom <= 6.0 else (-55.0 if zoom >= 13.0 else -50.0)

                return ExploreCommandPlan(
                    intent="navigation",
                    summary=f"Navigated to {geo_target.name} and highlighted region.",
                    commands=[
                        FlyToCommand(
                            location_query=geo_target.name,
                            latitude=geo_target.latitude,
                            longitude=geo_target.longitude,
                            zoom=zoom,
                            pitch=pitch,
                        ),
                        SetAOICommand(bbox=bbox),
                    ],
                )

        # 9. Direct City / Location Name ("New Delhi", "Mumbai", "Sriharikota", "China")
        # In Fast-Path, ONLY match against instant offline gazetteer to prevent random OSM fuzzy street matches
        direct_geo = GeoResolver.resolve(clean, allow_online=False)
        if direct_geo and direct_geo.confidence >= 0.9:
            from exploration.ai_schemas import FlyToCommand, SetAOICommand
            bbox = direct_geo.bbox or [direct_geo.longitude - 0.08, direct_geo.latitude - 0.06, direct_geo.longitude + 0.08, direct_geo.latitude + 0.06]
            zoom = direct_geo.zoom or cls.calculate_zoom(bbox)
            pitch = -35.0 if zoom <= 6.0 else (-55.0 if zoom >= 13.0 else -50.0)

            return ExploreCommandPlan(
                intent="navigation",
                summary=f"Navigated to {direct_geo.name} and highlighted region.",
                commands=[
                    FlyToCommand(
                        location_query=direct_geo.name,
                        latitude=direct_geo.latitude,
                        longitude=direct_geo.longitude,
                        zoom=zoom,
                        pitch=pitch,
                    ),
                    SetAOICommand(bbox=bbox),
                ],
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

    @classmethod
    def calculate_zoom(cls, bbox: Optional[List[float]], default: float = 11.5) -> float:
        """Determines best camera altitude/zoom based on the spatial bounding envelope."""
        if not bbox or len(bbox) < 4:
            return default
        span = max(abs(bbox[2] - bbox[0]), abs(bbox[3] - bbox[1]))
        if span > 25.0:
            return 3.5
        elif span > 10.0:
            return 4.5
        elif span > 3.0:
            return 6.0
        elif span > 0.5:
            return 10.0
        elif span > 0.05:
            return 12.5
        else:
            return 15.5

