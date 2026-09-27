"""
TRINETRA / Shanetra Geospatial Exploration Engine
Unit Tests: Temporal Observation Normalizer
Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
"""

import pytest
from exploration.temporal.normalizer import (
    ObservationSummary,
    ObservationDetails,
    ObservationNormalizer,
)


def test_normalize_raw_dict():
    raw_feature = {
        "id": "S2A_MSIL2A_20260315_NAGPUR",
        "collection": "sentinel-2-l2a",
        "properties": {
            "datetime": "2026-03-15T05:45:00Z",
            "eo:cloud_cover": 12.34,
            "platform": "Sentinel-2A",
        },
        "bbox": [79.0, 21.0, 79.2, 21.2],
        "assets": {
            "visual": {"href": "https://data.copernicus.eu/visual.tif"},
            "thumbnail": {"href": "https://data.copernicus.eu/thumb.png"},
        },
    }

    summary = ObservationNormalizer.to_summary(raw_feature)
    assert isinstance(summary, ObservationSummary)
    assert summary.id == "S2A_MSIL2A_20260315_NAGPUR"
    assert summary.collection == "sentinel-2-l2a"
    assert summary.datetime == "2026-03-15T05:45:00Z"
    assert summary.cloud_cover == 12.3
    assert summary.platform == "Sentinel-2A"
    assert summary.bbox == [79.0, 21.0, 79.2, 21.2]
    assert summary.thumbnail == "https://data.copernicus.eu/thumb.png"
    assert "visual" in summary.asset_keys


def test_normalize_details():
    raw_feature = {
        "id": "S2B_MSIL2A_20260401_MUMBAI",
        "collection": "sentinel-2-l2a",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[72.8, 18.9], [73.0, 18.9], [73.0, 19.1], [72.8, 19.1], [72.8, 18.9]]],
        },
        "properties": {
            "datetime": "2026-04-01T06:00:00Z",
            "eo:cloud_cover": 4.5,
            "platform": "Sentinel-2B",
        },
        "assets": {
            "visual": {"href": "https://example.com/vis.tif", "type": "image/tiff"},
        },
    }

    details = ObservationNormalizer.to_details(raw_feature)
    assert isinstance(details, ObservationDetails)
    assert details.id == "S2B_MSIL2A_20260401_MUMBAI"
    assert details.geometry is not None
    assert details.geometry["type"] == "Polygon"
    assert details.cloud_cover == 4.5
    assert "visual" in details.assets
