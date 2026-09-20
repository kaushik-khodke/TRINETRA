"""
Contract tests for AnalysisEngineService, job execution lifecycle, cancellation, and REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from analysis_engine.schemas import AnalysisRequest, AnalysisMode
from analysis_engine.service import analysis_engine_service
from analysis_engine.models import RunStatus

client = TestClient(app)


def test_service_create_and_cancel_run():
    req = AnalysisRequest(
        query="Bi-temporal change evaluation",
        mode=AnalysisMode.BI_TEMPORAL,
    )
    run = analysis_engine_service.create_run(req)
    assert run.run_id.startswith("run_")
    assert run.status == RunStatus.QUEUED

    # Cancellation
    cancelled = analysis_engine_service.cancel_run(run.run_id)
    assert cancelled is True
    assert run.status == RunStatus.CANCELLED


def test_service_sync_pipeline_execution():
    req = AnalysisRequest(
        query="Evaluate land change",
        mode=AnalysisMode.BI_TEMPORAL,
        observation_a_id="obs_01",
        observation_b_id="obs_02",
        aoi={"type": "Polygon", "coordinates": [[[79.0, 21.0], [79.1, 21.0], [79.1, 21.1], [79.0, 21.1], [79.0, 21.0]]]},
    )
    run = analysis_engine_service.create_run(req)
    result = analysis_engine_service._execute_pipeline_sync(run, req)

    assert result.status == "completed"
    assert result.mode == AnalysisMode.BI_TEMPORAL
    assert len(result.findings) >= 1
    assert "evidence" in result.dict()
    assert len(result.artifacts) >= 2


def test_api_enqueue_and_poll_status():
    payload = {
        "query": "Show urban growth between observations",
        "mode": "BI_TEMPORAL",
        "observation_a_id": "obs_01",
        "observation_b_id": "obs_02",
    }
    # 1. Enqueue
    resp = client.post("/api/v1/explore/analysis", json=payload)
    assert resp.status_code == 202
    data = resp.json()
    run_id = data["run_id"]
    assert data["status"] in ("queued", "running", "completed")

    # 2. Poll status
    status_resp = client.get(f"/api/v1/explore/analysis/{run_id}")
    assert status_resp.status_code == 200
    st_data = status_resp.json()
    assert st_data["run_id"] == run_id
    assert "progress" in st_data


def test_api_validate_endpoint():
    payload = {
        "query": "Check feasibility",
        "mode": "BI_TEMPORAL",
    }
    resp = client.post("/api/v1/explore/analysis/validate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "valid" in data
    assert "estimated_pixel_count" in data


def test_api_cancel_endpoint():
    req = AnalysisRequest(query="Long running job", mode=AnalysisMode.BI_TEMPORAL)
    run = analysis_engine_service.create_run(req)

    resp = client.post(f"/api/v1/explore/analysis/{run.run_id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"
