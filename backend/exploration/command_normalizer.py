"""
TRINETRA / Shanetra Geospatial Exploration Engine
AI Command Normalizer
Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
Deterministic normalization of command synonyms, layer aliases, numeric percentages, and deduplication.
"""

import re
from typing import Any, Dict, List, Optional
from exploration.fallback_parser import LAYER_ALIASES


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
