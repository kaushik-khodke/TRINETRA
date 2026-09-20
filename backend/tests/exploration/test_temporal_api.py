"""
TRINETRA / Shanetra Geospatial Exploration Engine
Contract & Integration Tests: Temporal Exploration API Endpoints
Phase 4: Temporal Exploration, AOI Selection & Observation Comparison
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_aoi_validation_valid():
    aoi_payload = {
        "aoi": {
            "type": "Polygon",
            "coordinates": [
                [
                    [79.0, 21.0],
                    [79.2, 21.0],
                    [79.2, 21.2],
                    [79.0, 21.2],
                    [79.0, 21.0],
                ]
            ],
        }
    }
    resp = client.post("/api/v1/explore/aoi/validate", json=aoi_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["area_km2"] > 0
    assert data["vertex_count"] == 5


def test_api_aoi_validation_invalid_self_intersecting():
    aoi_payload = {
        "aoi": {
            "type": "Polygon",
            "coordinates": [
                [
                    [0.0, 0.0],
                    [2.0, 2.0],
                    [0.0, 2.0],
                    [2.0, 0.0],
                    [0.0, 0.0],
                ]
            ],
        }
    }
    resp = client.post("/api/v1/explore/aoi/validate", json=aoi_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False
    assert len(data["errors"]) > 0


def test_api_search_observations():
    payload = {
        "start_datetime": "2026-01-01T00:00:00Z",
        "end_datetime": "2026-06-01T00:00:00Z",
        "collections": ["sentinel-2-l2a"],
        "limit": 10,
    }
    resp = client.post("/api/v1/explore/observations/search", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "observations" in data
    assert "request_id" in data
    assert isinstance(data["observations"], list)


def test_api_comparison_validate():
    payload = {
        "observation_a_id": "obs_1",
        "observation_b_id": "obs_1",
        "mode": "split",
    }
    resp = client.post("/api/v1/explore/comparison/validate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    # Comparing with itself must fail
    assert data["compatible"] is False
    assert len(data["errors"]) > 0
