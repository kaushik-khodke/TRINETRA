"""
TRINETRA Analysis Engine — REST API Endpoints
Provides endpoints for enqueuing analysis runs, polling real-time progress,
retrieving validated evidence packs, serving artifacts, and cancelling runs.
"""

import os
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from fastapi.responses import FileResponse
from typing import Dict, Any, Optional

from analysis_engine.schemas import (
    AnalysisRequest,
    AnalysisResult,
    AnalysisValidationRequest,
    AnalysisValidationResponse,
)
from analysis_engine.models import RunStatus
from analysis_engine.service import analysis_engine_service
from config.settings import settings

router = APIRouter(prefix="/api/v1/explore/analysis", tags=["Explore Analysis Engine"])



@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def enqueue_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Enqueues a new Earth Observation analysis run.
    Returns immediately with run_id and status: queued.
    """
    run = analysis_engine_service.create_run(request)

    # Launch non-blocking background analysis task
    background_tasks.add_task(
        analysis_engine_service.execute_run_async,
        run.run_id,
        request,
    )

    return {
        "run_id": run.run_id,
        "request_id": run.request_id,
        "status": run.status.value,
        "mode": run.mode,
        "progress": run.progress.dict() if hasattr(run, "progress") and run.progress else {
            "stage": "validating",
            "message": "Initializing analysis pipeline...",
            "step_index": 1,
            "step_number": 1,
            "total_steps": 7,
            "percent": 0,
        },
        "created_at": run.created_at,
    }


@router.get("/{run_id}")
async def get_analysis_status(run_id: str) -> Dict[str, Any]:
    """
    Returns the current execution status, discrete progress stage, and results if completed.
    """
    run = analysis_engine_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Analysis run '{run_id}' not found.")

    response = {
        "run_id": run.run_id,
        "status": run.status.value,
        "mode": run.mode,
        "progress": run.progress.dict(),
        "created_at": run.created_at,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
        "artifacts": [a.dict() for a in run.artifacts],
    }

    if run.status == RunStatus.COMPLETED and run.result_data:
        response["result"] = run.result_data

    if run.status == RunStatus.FAILED and run.error:
        response["error"] = run.error

    return response


@router.get("/{run_id}/evidence")
async def get_analysis_evidence(run_id: str) -> Dict[str, Any]:
    """
    Returns the complete, validated EvidencePack for an analysis run.
    """
    run = analysis_engine_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Analysis run '{run_id}' not found.")

    if run.status != RunStatus.COMPLETED or not run.result_data:
        raise HTTPException(status_code=400, detail=f"Analysis run '{run_id}' has not completed.")

    return run.result_data.get("evidence", {})


@router.get("/artifacts/{run_id}/{filename}")
async def get_analysis_artifact_file(run_id: str, filename: str):
    """
    Serves a persisted analysis artifact (GeoJSON, PNG preview, JSON manifest) from disk.
    """
    # Security: prevent path traversal
    clean_filename = os.path.basename(filename)
    artifact_path = os.path.join(settings.analysis_artifacts_dir, run_id, clean_filename)

    if not os.path.exists(artifact_path):
        raise HTTPException(status_code=404, detail=f"Artifact '{filename}' not found for run '{run_id}'.")

    media_type = "application/json"
    if clean_filename.endswith(".png"):
        media_type = "image/png"
    elif clean_filename.endswith(".geojson"):
        media_type = "application/geo+json"
    elif clean_filename.endswith(".tif") or clean_filename.endswith(".tiff"):
        media_type = "image/tiff"

    return FileResponse(artifact_path, media_type=media_type)


@router.post("/{run_id}/cancel")
async def cancel_analysis(run_id: str) -> Dict[str, Any]:
    """
    Gracefully cancels a running or queued analysis run.
    """
    success = analysis_engine_service.cancel_run(run_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Analysis run '{run_id}' not found.")

    return {
        "run_id": run_id,
        "status": "cancelled",
        "message": "Analysis run cancellation requested.",
    }


@router.post("/validate")
async def validate_analysis_request(
    request: AnalysisRequest,
) -> AnalysisValidationResponse:
    """
    Performs fast pre-flight compatibility and prerequisite validation.
    """
    return analysis_engine_service.validate_request(request)
