"""
TRINETRA / Shanetra Geospatial Exploration Engine
Layer Governance & Security Policies
Phase 2: Prevents uncontrolled layer activation, enforces rendering safety, and protects against path traversal.
"""

import math
import re
from typing import List, Optional, Tuple, Set
from exploration.models import ExploreLayer

# Engineering limits preventing renderer overload & memory exhaustion
MAX_ACTIVE_BASE_LAYERS = 1
MAX_ACTIVE_IMAGERY_LAYERS = 2
MAX_ACTIVE_ANALYTICAL_LAYERS = 4
MAX_ACTIVE_SYSTEM_LAYERS = 0  # Standard users cannot activate raw system/debug layers

SAFE_ASSET_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.:]{1,128}$")


class LayerPolicyEngine:
    """Deterministic governance rules for layer activation and visibility."""

    @staticmethod
    def clamp_opacity(opacity: float) -> float:
        """Clamps opacity strictly to [0.0, 1.0]. Replaces NaN or invalid numbers with 1.0."""
        if opacity is None or math.isnan(opacity) or math.isinf(opacity):
            return 1.0
        return max(0.0, min(1.0, float(opacity)))

    @staticmethod
    def validate_safe_asset_id(asset_id: str) -> bool:
        """Validates that asset_id contains only alphanumeric and safe characters. Rejects traversal attempts."""
        if not asset_id or not isinstance(asset_id, str):
            return False
        if ".." in asset_id or "/" in asset_id or "\\" in asset_id:
            return False
        return bool(SAFE_ASSET_ID_REGEX.match(asset_id))

    @staticmethod
    def is_zoom_supported(layer: ExploreLayer, zoom: float) -> bool:
        """Determines if the requested zoom level falls within the layer's supported range."""
        if zoom is None:
            return True
        return layer.min_zoom <= zoom <= layer.max_zoom

    @classmethod
    def can_activate_layer(
        cls,
        layer: ExploreLayer,
        active_layers: List[ExploreLayer],
        is_ai_caller: bool = False,
        current_zoom: Optional[float] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates whether a layer can be safely activated under current session state.
        Returns (is_allowed: bool, rejection_reason: Optional[str]).
        """
        # 1. Enabled check
        if not layer.enabled:
            return False, f"Layer '{layer.id}' is administratively disabled."

        # 2. Permission boundary
        if not is_ai_caller and not layer.user_controllable:
            return False, f"Layer '{layer.id}' is restricted from direct user activation."
        if is_ai_caller and not layer.ai_controllable:
            return False, f"Layer '{layer.id}' cannot be activated by automated AI commands."

        # 3. Zoom-gating check
        if current_zoom is not None and not cls.is_zoom_supported(layer, current_zoom):
            return False, (
                f"Current zoom ({current_zoom:.1f}) is outside layer '{layer.id}' "
                f"supported range [{layer.min_zoom}, {layer.max_zoom}]."
            )

        # 4. Maximum simultaneous layer limit per category
        category = layer.category.lower()
        active_in_category = [l for l in active_layers if l.category.lower() == category and l.id != layer.id]

        if category == "base":
            if len(active_in_category) >= MAX_ACTIVE_BASE_LAYERS:
                return False, f"Maximum active base layers limit ({MAX_ACTIVE_BASE_LAYERS}) reached."
        elif category == "imagery":
            if len(active_in_category) >= MAX_ACTIVE_IMAGERY_LAYERS:
                return False, f"Maximum active imagery layers limit ({MAX_ACTIVE_IMAGERY_LAYERS}) reached."
        elif category == "analytical":
            if len(active_in_category) >= MAX_ACTIVE_ANALYTICAL_LAYERS:
                return False, f"Maximum active analytical layers limit ({MAX_ACTIVE_ANALYTICAL_LAYERS}) reached."
        elif category == "system":
            if not is_ai_caller and len(active_in_category) >= MAX_ACTIVE_SYSTEM_LAYERS:
                return False, "System layers cannot be activated by standard users."

        return True, None
