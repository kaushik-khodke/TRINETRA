"""
Contract tests for AnalysisEngineService, job execution lifecycle, cancellation, and REST API endpoints.
"""

from analysis_engine.schemas import AnalysisRequest, AnalysisMode
from analysis_engine.service import analysis_engine_service
from analysis_engine.models import RunStatus


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

