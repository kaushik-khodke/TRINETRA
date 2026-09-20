"""
Unit Tests — Local Raster Provider
Verifies lazy directory indexing, bounding box spatial filtering, and asset retrieval.
"""

import os
import pytest
from exploration.local_provider import LocalRasterProvider
from exploration.schemas import ExploreSearchRequest


@pytest.fixture
def local_provider():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sample_dir = os.path.join(base_dir, "sample_data", "explore")
    return LocalRasterProvider(data_dirs=[sample_dir])


def test_indexing_discovers_fixtures(local_provider):
    assert local_provider.status() == "ready"
    items = local_provider.search(ExploreSearchRequest(limit=10))
    assert len(items) >= 2

    item_ids = [i.id for i in items]
    assert any("nagpur" in id_str for id_str in item_ids)
    assert any("mumbai" in id_str for id_str in item_ids)


def test_spatial_bbox_search_filtering(local_provider):
    # Search over Nagpur [78.9, 20.9, 79.3, 21.3]
    req = ExploreSearchRequest(bbox=[78.9, 20.9, 79.3, 21.3], limit=10)
    results = local_provider.search(req)

    assert len(results) >= 1
    assert "nagpur" in results[0].id.lower()


def test_disjoint_bbox_returns_empty(local_provider):
    # Search in Antarctica
    req = ExploreSearchRequest(bbox=[0.0, -85.0, 10.0, -80.0], limit=10)
    results = local_provider.search(req)
    assert len(results) == 0


def test_get_metadata_by_asset_id(local_provider):
    meta = local_provider.get_metadata("local_sentinel2_nagpur_truecolor")
    assert meta is not None
    assert meta["width"] == 256
    assert meta["height"] == 256
    assert meta["bands"] == 4
    assert meta["crs"] == "EPSG:4326"
