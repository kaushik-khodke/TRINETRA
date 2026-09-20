"""
Unit Tests — Exploration Models & Schemas
Tests internal data structures, Pydantic validations, and bbox constraints.
"""

import pytest
from exploration.models import EOAsset, EOItem, ExploreLayer, RasterSource
from exploration.schemas import ExploreSearchRequest, ExploreSearchResponse, LayerResponse


def test_eo_asset_and_item_creation():
    asset = EOAsset(
        id="B04",
        href="http://example.com/b04.tif",
        role="visual",
        title="Red Band",
        bands=["B04"],
    )
    item = EOItem(
        id="S2A_TEST_001",
        collection="sentinel-2-l2a",
        datetime="2026-09-20T10:00:00Z",
        bbox=[78.5, 20.5, 79.5, 21.5],
        cloud_cover=4.2,
        assets={"B04": asset},
        provider="local",
    )

    assert item.id == "S2A_TEST_001"
    assert len(item.assets) == 1
    assert item.assets["B04"].role == "visual"
    assert item.cloud_cover == 4.2


def test_explore_search_request_bbox_validation():
    # Valid bbox: [min_lon, min_lat, max_lon, max_lat]
    req = ExploreSearchRequest(bbox=[72.0, 18.0, 73.0, 19.0], limit=20)
    assert req.bbox == [72.0, 18.0, 73.0, 19.0]
    assert req.limit == 20

    # Invalid bbox: min_lon > max_lon
    with pytest.raises(ValueError):
        ExploreSearchRequest(bbox=[80.0, 18.0, 70.0, 19.0])

    # Invalid bbox: latitude out of bounds
    with pytest.raises(ValueError):
        ExploreSearchRequest(bbox=[70.0, -95.0, 75.0, 19.0])


def test_explore_search_request_hard_limit():
    # Exceeding 50 should raise ValidationError
    with pytest.raises(ValueError):
        ExploreSearchRequest(limit=51)

    # 0 or negative limit should raise ValidationError
    with pytest.raises(ValueError):
        ExploreSearchRequest(limit=0)
