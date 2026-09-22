"""
Integration tests for FastAPI REST Endpoints in app/routes/intelligence.py.
Uses TestClient to validate HTTP contracts, schema formatting, and status codes.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from intelligence.service import intelligence_service
from intelligence.models import PersistentFinding, EOEvent, EventState


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_intelligence_status_endpoint(client):
    resp = client.get("/api/v1/explore/intelligence/ai/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["available"] is True
    assert "events_count" in data


def test_list_events_and_findings(client):
    # Ingest a sample finding to seed data
    f = PersistentFinding(
        finding_id="fnd_api_01",
        investigation_id="inv_api_01",
        type="test_type",
        label="Test API Finding",
        bounding_box=[79.0, 21.0, 79.1, 21.1],
        confidence=0.85,
        semantic_class="INFRASTRUCTURE",
        metrics={"change_percentage": 5.2},
    )
    intelligence_service.ingest_finding(f)

    # Get events
    resp = client.get("/api/v1/explore/intelligence/events")
    assert resp.status_code == 200
    events = resp.json()
    assert isinstance(events, list)
    assert len(events) >= 1

    # Get findings
    resp_f = client.get("/api/v1/explore/intelligence/findings")
    assert resp_f.status_code == 200
    findings = resp_f.json()
    assert isinstance(findings, list)
    assert len(findings) >= 1


def test_search_endpoint(client):
    payload = {
        "query": "infrastructure change",
        "limit": 5,
    }
    resp = client.post("/api/v1/explore/intelligence/search", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert "total" in data


def test_regions_and_hotspots(client):
    resp_r = client.get("/api/v1/explore/intelligence/regions")
    assert resp_r.status_code == 200
    assert isinstance(resp_r.json(), list)

    resp_h = client.get("/api/v1/explore/intelligence/hotspots")
    assert resp_h.status_code == 200
    assert isinstance(resp_h.json(), list)


def test_monitors_crud_api(client):
    payload = {
        "name": "API Test Monitor",
        "bbox": [79.0, 21.0, 79.2, 21.2],
        "trigger_condition": {"op": ">", "field": "confidence", "value": 0.8},
        "enabled": True,
    }
    resp = client.post("/api/v1/explore/intelligence/monitors", json=payload)
    assert resp.status_code == 200
    created = resp.json()
    assert created["name"] == "API Test Monitor"
    mon_id = created["monitor_id"]

    # List
    resp_list = client.get("/api/v1/explore/intelligence/monitors")
    assert resp_list.status_code == 200
    ids = [m["monitor_id"] for m in resp_list.json()]
    assert mon_id in ids

    # Toggle
    resp_toggle = client.post(f"/api/v1/explore/intelligence/monitors/{mon_id}/toggle")
    assert resp_toggle.status_code == 200
    assert resp_toggle.json()["enabled"] is False


def test_templates_api(client):
    tmpl_payload = {
        "name": "Rapid Infrastructure Growth",
        "question": "Assess new construction footprints in selected sector",
        "analysis_mode": "BI_TEMPORAL",
        "required_evidence": ["change_map"],
    }
    client.post("/api/v1/explore/intelligence/templates", json=tmpl_payload)

    resp = client.get("/api/v1/explore/intelligence/templates")
    assert resp.status_code == 200
    templates = resp.json()
    assert isinstance(templates, list)
    assert len(templates) >= 1
