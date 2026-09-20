"""
Test Suite: Explore AI REST API Contract (Test Group AB)
Verifies FastAPI endpoints /api/v1/explore/ai/status and /api/v1/explore/ai/query.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_ai_status_endpoint():
    response = client.get("/api/v1/explore/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert "available" in data
    assert "structured_output" in data
    assert "router_model" in data
    assert "planner_model" in data
    assert data["structured_output"] is True


def test_api_ai_query_fast_path_reset():
    payload = {
        "query": "reset",
        "active_layer_ids": ["layer-base-dark"],
    }
    response = client.post("/api/v1/explore/ai/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["fast_path"] is True
    assert data["intent"] == "reset"
    assert len(data["commands"]) == 1
    assert data["commands"][0]["type"] == "RESET_VIEW"
    assert data["state_patch"]["camera"] is not None


def test_api_ai_query_empty_rejected():
    payload = {
        "query": "   ",
    }
    response = client.post("/api/v1/explore/ai/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["error_code"] == "EXPLORE_QUERY_EMPTY"


def test_api_ai_query_oversized_rejected():
    payload = {
        "query": "x" * 501,
    }
    response = client.post("/api/v1/explore/ai/query", json=payload)
    # FastAPI schema validation catches max_length=500 and returns 422
    assert response.status_code in (422, 200)
    if response.status_code == 200:
        data = response.json()
        assert data["error_code"] == "EXPLORE_QUERY_TOO_LONG"
