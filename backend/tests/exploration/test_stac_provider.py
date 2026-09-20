"""
Unit Tests — STAC Provider
Tests GeoJSON item normalization, mocked spatial queries, and network failure tolerance.
"""

import pytest
from unittest.mock import patch, MagicMock
import requests
from exploration.stac_provider import STACProvider
from exploration.schemas import ExploreSearchRequest


MOCK_STAC_FEATURE = {
    "id": "S2A_MSIL2A_20260818T054651_N0500_R105_T43QDF_20260818T082000",
    "type": "Feature",
    "collection": "sentinel-2-l2a",
    "bbox": [78.8, 20.8, 79.5, 21.5],
    "geometry": {
        "type": "Polygon",
        "coordinates": [[[78.8, 20.8], [79.5, 20.8], [79.5, 21.5], [78.8, 21.5], [78.8, 20.8]]]
    },
    "properties": {
        "datetime": "2026-08-18T05:46:51Z",
        "eo:cloud_cover": 6.8,
        "platform": "Sentinel-2A",
    },
    "assets": {
        "visual": {
            "href": "https://dataspace.copernicus.eu/eodata/S2A/TCI.tif",
            "type": "image/tiff; application=geotiff; profile=cloud-optimized",
            "roles": ["visual"],
            "title": "True Color Image",
        },
        "thumbnail": {
            "href": "https://dataspace.copernicus.eu/eodata/S2A/thumbnail.jpg",
            "type": "image/jpeg",
            "roles": ["thumbnail"],
        }
    },
    "links": [{"rel": "self", "href": "https://stac.dataspace.copernicus.eu/v1/items/S2A"}]
}


def test_stac_item_normalization():
    item = STACProvider.normalize_stac_item(MOCK_STAC_FEATURE)
    assert item is not None
    assert item.id == "S2A_MSIL2A_20260818T054651_N0500_R105_T43QDF_20260818T082000"
    assert item.collection == "sentinel-2-l2a"
    assert item.cloud_cover == 6.8
    assert item.provider == "copernicus"
    assert item.thumbnail_url == "https://dataspace.copernicus.eu/eodata/S2A/thumbnail.jpg"
    assert "visual" in item.assets
    assert item.assets["visual"].role == "visual"


@patch("requests.post")
def test_mocked_stac_search_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"features": [MOCK_STAC_FEATURE]}
    mock_post.return_value = mock_resp

    provider = STACProvider(endpoint_url="http://mock-stac.local/v1")
    req = ExploreSearchRequest(bbox=[78.8, 20.8, 79.5, 21.5], limit=5)
    results = provider.search(req)

    assert len(results) == 1
    assert results[0].id == MOCK_STAC_FEATURE["id"]


@patch("requests.post")
def test_mocked_stac_search_timeout_tolerance(mock_post):
    mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")

    provider = STACProvider(endpoint_url="http://mock-stac.local/v1")
    req = ExploreSearchRequest(limit=5)
    # Should catch timeout and return empty list cleanly without raising exception
    results = provider.search(req)
    assert results == []


@patch("requests.post")
def test_mocked_stac_search_500_error_tolerance(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    mock_post.return_value = mock_resp

    provider = STACProvider(endpoint_url="http://mock-stac.local/v1")
    req = ExploreSearchRequest(limit=5)
    results = provider.search(req)
    assert results == []
