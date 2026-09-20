"""
Unit Tests — Layer Governance Policies
Tests layer limits, zoom-gating, security sanitization, and permission boundaries.
"""

import math
import pytest
from exploration.models import ExploreLayer
from exploration.policies import (
    LayerPolicyEngine,
    MAX_ACTIVE_IMAGERY_LAYERS,
    MAX_ACTIVE_BASE_LAYERS,
)


def test_opacity_clamping():
    assert LayerPolicyEngine.clamp_opacity(0.7) == 0.7
    assert LayerPolicyEngine.clamp_opacity(-0.5) == 0.0
    assert LayerPolicyEngine.clamp_opacity(1.5) == 1.0
    assert LayerPolicyEngine.clamp_opacity(float("nan")) == 1.0
    assert LayerPolicyEngine.clamp_opacity(float("inf")) == 1.0


def test_asset_id_path_traversal_protection():
    assert LayerPolicyEngine.validate_safe_asset_id("valid_asset_123") is True
    assert LayerPolicyEngine.validate_safe_asset_id("sentinel-2-l2a.tif") is True

    # Malicious traversal attempts
    assert LayerPolicyEngine.validate_safe_asset_id("../../etc/passwd") is False
    assert LayerPolicyEngine.validate_safe_asset_id("..\\..\\windows\\system32") is False
    assert LayerPolicyEngine.validate_safe_asset_id("asset/subfolder") is False
    assert LayerPolicyEngine.validate_safe_asset_id("") is False


def test_layer_activation_limits():
    l1 = ExploreLayer(id="img1", name="Img 1", category="imagery", user_controllable=True)
    l2 = ExploreLayer(id="img2", name="Img 2", category="imagery", user_controllable=True)
    l3 = ExploreLayer(id="img3", name="Img 3", category="imagery", user_controllable=True)

    # 1st imagery layer allowed
    allowed, _ = LayerPolicyEngine.can_activate_layer(l1, active_layers=[])
    assert allowed is True

    # 2nd imagery layer allowed
    allowed, _ = LayerPolicyEngine.can_activate_layer(l2, active_layers=[l1])
    assert allowed is True

    # 3rd imagery layer exceeds MAX_ACTIVE_IMAGERY_LAYERS (2)
    allowed, reason = LayerPolicyEngine.can_activate_layer(l3, active_layers=[l1, l2])
    assert allowed is False
    assert "limit" in reason.lower()


def test_zoom_gating():
    detail_layer = ExploreLayer(
        id="high_res",
        name="High Res",
        category="imagery",
        min_zoom=10,
        max_zoom=18,
        user_controllable=True,
    )

    # Low zoom (out of range)
    allowed, reason = LayerPolicyEngine.can_activate_layer(
        detail_layer, active_layers=[], current_zoom=5.0
    )
    assert allowed is False
    assert "zoom" in reason.lower()

    # Valid zoom
    allowed, _ = LayerPolicyEngine.can_activate_layer(
        detail_layer, active_layers=[], current_zoom=12.0
    )
    assert allowed is True
