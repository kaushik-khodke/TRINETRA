"""
TRINETRA / Shanetra Geospatial Exploration Engine
AI Command Normalizer
Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
Deterministic normalization of command synonyms, layer aliases, numeric percentages, and deduplication.
"""

import re
from typing import Any, Dict, List, Optional
from exploration.fallback_parser import LAYER_ALIASES
from exploration.ai_schemas import SetAOICommand


PERCENTAGE_REGEX = re.compile(r"(\d+(?:\.\d+)?)\s*(?:%|percent)", re.IGNORECASE)


class CommandNormalizer:
    """Normalizes natural-language phrasing into canonical structures."""

    @staticmethod
    def normalize_percentage(text: str) -> Optional[float]:
        """Extracts and normalizes percentage into a 0.0 - 1.0 float."""
        match = PERCENTAGE_REGEX.search(text)
        if match:
            val = float(match.group(1))
            return max(0.0, min(1.0, val / 100.0))
        return None

    @staticmethod
    def resolve_layer_alias(raw_layer_name: str) -> Optional[str]:
        """Resolves common natural language aliases to canonical layer IDs."""
        if not raw_layer_name:
            return None
        clean = raw_layer_name.strip().lower()
        if clean in LAYER_ALIASES:
            return LAYER_ALIASES[clean]
        for alias, layer_id in LAYER_ALIASES.items():
            if alias in clean:
                return layer_id
        if clean.startswith("layer-"):
            return clean
        return None

    @classmethod
    def deduplicate_commands(cls, commands: List[Any]) -> List[Any]:
        """Deduplicates redundant consecutive or identical layer actions."""
        seen_keys = set()
        deduped = []
        for cmd in commands:
            cmd_type = getattr(cmd, "type", None) or (cmd.get("type") if isinstance(cmd, dict) else None)
            layer_id = getattr(cmd, "layer_id", None) or (cmd.get("layer_id") if isinstance(cmd, dict) else None)
            key = f"{cmd_type}:{layer_id}" if layer_id else f"{cmd_type}"
            if key not in seen_keys or cmd_type in ("ZOOM_IN", "ZOOM_OUT"):
                seen_keys.add(key)
                deduped.append(cmd)
        return deduped

    @classmethod
    def sanitize_and_enrich_commands(cls, commands: List[Any]) -> List[Any]:
        """
        Deduplicates commands and repairs common LLM structural omissions:
        - If SET_AOI has no bbox or geometry, derives bbox from accompanying FLY_TO coordinates.
        - If SET_AOI has no accompanying FLY_TO and no bbox/geometry, safely drops the malformed command.
        """
        deduped = cls.deduplicate_commands(commands)
        fly_target = None
        for cmd in deduped:
            cmd_type = getattr(cmd, "type", None) or (cmd.get("type") if isinstance(cmd, dict) else None)
            if cmd_type == "FLY_TO":
                lat = getattr(cmd, "latitude", None) or (cmd.get("latitude") if isinstance(cmd, dict) else None)
                lon = getattr(cmd, "longitude", None) or (cmd.get("longitude") if isinstance(cmd, dict) else None)
                if lat is not None and lon is not None:
                    fly_target = (float(lat), float(lon))
                    break

        repaired = []
        for cmd in deduped:
            cmd_type = getattr(cmd, "type", None) or (cmd.get("type") if isinstance(cmd, dict) else None)
            if cmd_type == "SET_AOI":
                geom = getattr(cmd, "geometry", None) or (cmd.get("geometry") if isinstance(cmd, dict) else None)
                bbox = getattr(cmd, "bbox", None) or (cmd.get("bbox") if isinstance(cmd, dict) else None)
                if not geom and not bbox:
                    if fly_target:
                        lat, lon = fly_target
                        derived_bbox = [round(lon - 0.1, 4), round(lat - 0.1, 4), round(lon + 0.1, 4), round(lat + 0.1, 4)]
                        if isinstance(cmd, dict):
                            cmd["bbox"] = derived_bbox
                            repaired.append(cmd)
                        else:
                            repaired.append(SetAOICommand(bbox=derived_bbox))
                        continue
                    else:
                        continue
            repaired.append(cmd)
        return repaired
