"""
TRINETRA Phase 6 — Tests for Investigation REST API
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_validate_investigation():
    payload = {
        "question": "Explain major changes and potential built-up expansion",
        "observation_ids": ["obs_1", "obs_2"],
    }
    response = client.post("/api/v1/explore/investigations/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["intent"] == "BUILT_UP_CHANGE"
    assert len(data["planned_specialists"]) > 0


def test_api_enqueue_and_get_details():
    payload = {
        "question": "What happened in this area between these observations?",
        "observation_ids": ["obs_alpha", "obs_beta"],
    }
    # Enqueue investigation
    res_post = client.post("/api/v1/explore/investigations", json=payload)
    assert res_post.status_code == 202
    data_post = res_post.json()
    inv_id = data_post["investigation_id"]
    assert inv_id.startswith("inv_")

    # Get details
    res_get = client.get(f"/api/v1/explore/investigations/{inv_id}")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["investigation_id"] == inv_id
    assert data_get["question"] == payload["question"]


def test_api_list_investigations():
    res = client.get("/api/v1/explore/investigations?limit=10")
    assert res.status_code == 200
    items = res.json()
    assert isinstance(items, list)


def test_api_analyst_notes():
    # Enqueue investigation first
    payload = {"question": "Check for industrial changes", "observation_ids": ["obs_1"]}
    res = client.post("/api/v1/explore/investigations", json=payload)
    inv_id = res.json()["investigation_id"]

    # Post note
    note_payload = {
        "investigation_id": inv_id,
        "text": "Ground survey confirms construction activity started November 2025.",
    }
    res_note = client.post(f"/api/v1/explore/investigations/{inv_id}/notes", json=note_payload)
    assert res_note.status_code == 201
    note_data = res_note.json()
    note_id = note_data["note_id"]
    assert note_data["text"] == note_payload["text"]

    # Get notes
    res_get_notes = client.get(f"/api/v1/explore/investigations/{inv_id}/notes")
    assert res_get_notes.status_code == 200
    notes_list = res_get_notes.json()
    assert any(n["note_id"] == note_id for n in notes_list)

    # Delete note
    res_del = client.delete(f"/api/v1/explore/investigations/{inv_id}/notes/{note_id}")
    assert res_del.status_code == 200
