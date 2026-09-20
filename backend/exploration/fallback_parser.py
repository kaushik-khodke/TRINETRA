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
    "sentinel 2": "layer-local_sentinel2_nagpur_truecolor",
    "sentinel-2": "layer-local_sentinel2_nagpur_truecolor",
    "s2": "layer-local_sentinel2_nagpur_truecolor",
    "optical": "layer-local_sentinel2_nagpur_truecolor",
    "optical satellite": "layer-local_sentinel2_nagpur_truecolor",
    "satellite layer": "layer-local_sentinel2_nagpur_truecolor",
    # Sentinel-1 SAR imagery
    "sentinel 1": "layer-local_sentinel1_mumbai_sar",
    "sentinel-1": "layer-local_sentinel1_mumbai_sar",
    "s1": "layer-local_sentinel1_mumbai_sar",
    "sar": "layer-local_sentinel1_mumbai_sar",
    "radar": "layer-local_sentinel1_mumbai_sar",
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

        # 1. Reset View
        if RESET_REGEX.match(clean):
            return ExploreCommandPlan(
                intent="reset",
                summary="Reset Shanetra globe to default perspective.",
                commands=[ResetViewCommand()],
            )

        # 2. Zoom In
        if ZOOM_IN_REGEX.match(clean):
            return ExploreCommandPlan(
                intent="view_control",
                summary="Zoomed into the active viewport.",
                commands=[ZoomInCommand(step=1.0)],
            )

        # 3. Zoom Out
        if ZOOM_OUT_REGEX.match(clean):
            return ExploreCommandPlan(
                intent="view_control",
                summary="Zoomed out to a wider perspective.",
                commands=[ZoomOutCommand(step=1.0)],
            )

        # 4. Show Layer
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

        # 5. Hide Layer
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
