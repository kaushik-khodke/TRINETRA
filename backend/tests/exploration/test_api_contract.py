"""
Integration Tests — FastAPI Explore API Contract
Verifies REST endpoints, HTTP status codes, headers, and error handling via TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_catalog_status():
    resp = client.get("/api/v1/explore/catalog/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "local_provider" in data
    assert "stac_provider" in data
    assert data["cache"] == "ready"


def test_api_search():
    resp = client.post("/api/v1/explore/search", json={"limit": 5, "provider": "local"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) >= 1


def test_api_layers():
    resp = client.get("/api/v1/explore/layers")
    assert resp.status_code == 200
    layers = resp.json()
    assert isinstance(layers, list)
    assert any(l["id"] == "layer-base-dark" for l in layers)


def test_api_raster_metadata():
    resp = client.get("/api/v1/explore/metadata/local_sentinel2_nagpur_truecolor")
    assert resp.status_code == 200
    meta = resp.json()
    assert meta["width"] == 256
    assert meta["height"] == 256
    assert meta["crs"] == "EPSG:4326"


def test_api_raster_metadata_path_traversal_blocked():
    resp = client.get("/api/v1/explore/metadata/..%2F..%2Fsecret")
    assert resp.status_code in [400, 404]


def test_api_tiles_endpoint():
    # Register layer first
    reg_resp = client.post("/api/v1/explore/layers/register?asset_id=local_sentinel2_nagpur_truecolor")
    assert reg_resp.status_code == 200

    # Request tile over Nagpur
    resp = client.get("/api/v1/explore/tiles/layer-local_sentinel2_nagpur_truecolor/8/184/112.png")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert "ETag" in resp.headers
    assert "public, max-age=" in resp.headers["cache-control"]


def test_api_tiles_invalid_coordinates_rejected():
    # Negative/overflowing coordinate
    resp = client.get("/api/v1/explore/tiles/layer-base-dark/2/100/100.png")
    assert resp.status_code == 400
