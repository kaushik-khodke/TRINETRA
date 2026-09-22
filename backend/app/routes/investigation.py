"""
TRINETRA Phase 6 — Investigation REST API Endpoints
Provides endpoints for enqueuing investigations, streaming/polling progress,
retrieving evidence graphs, findings, timelines, artifacts, and managing analyst notes.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, status, Query, Path
from fastapi.responses import FileResponse

from investigation.schemas import (
    InvestigationRequest,
    InvestigationValidationResponse,
)
from investigation.models import (
    Investigation,
    InvestigationStatus,
    AnalystNote,
)
from investigation.service import investigation_service
from config.settings import settings

logger = logging.getLogger("trinetra.routes.investigation")

router = APIRouter(prefix="/api/v1/explore/investigations", tags=["Explore Investigation Engine"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def enqueue_investigation(
    request: InvestigationRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Enqueues a new multi-specialist Earth-Observation investigation.
    Returns immediately with investigation_id and status: queued.
    """
    inv = investigation_service.create_investigation(request)

    # Launch non-blocking background execution
    background_tasks.add_task(
        investigation_service.run_investigation,
        inv.investigation_id,
    )

    return {
        "investigation_id": inv.investigation_id,
        "status": inv.status.value,
        "question": inv.question,
        "observation_ids": inv.observation_ids,
        "created_at": inv.created_at,
    }


@router.get("")
async def list_investigations(
    limit: int = Query(50, ge=1, le=100),
) -> List[Dict[str, Any]]:
    """Lists recent investigations in descending chronological order."""
    invs = investigation_service.list_investigations(limit=limit)
    return [
        {
            "investigation_id": inv.investigation_id,
            "question": inv.question,
            "status": inv.status.value,
            "progress": inv.progress.dict(),
            "observation_ids": inv.observation_ids,
            "created_at": inv.created_at,
            "completed_at": inv.completed_at,
        }
        for inv in invs
    ]


@router.post("/validate")
async def validate_investigation(
    request: InvestigationRequest,
) -> InvestigationValidationResponse:
    """Pre-flight check assessing enquiry viability, intent, and compute cost."""
    return investigation_service.validate_request(request)


@router.get("/{investigation_id}")
async def get_investigation_details(
    investigation_id: str = Path(..., description="Unique investigation ID"),
) -> Dict[str, Any]:
    """Retrieves current state, progress, and synthesized findings for an investigation."""
    inv = investigation_service.get_investigation(investigation_id)
    if not inv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{investigation_id}' was not found.",
        )

    res_data = inv.result_data or {}

    return {
        "investigation_id": inv.investigation_id,
        "question": inv.question,
        "status": inv.status.value,
        "progress": inv.progress.dict(),
        "created_at": inv.created_at,
        "started_at": inv.started_at,
        "completed_at": inv.completed_at,
        "plan": res_data.get("plan"),
        "findings": res_data.get("findings", []),
        "hypotheses": res_data.get("hypotheses", []),
        "conflicts": res_data.get("conflicts", []),
        "conclusion": res_data.get("conclusion"),
        "limitations": res_data.get("limitations", []),
        "artifacts": [a.dict() for a in inv.artifacts],
        "error": inv.error,
    }


@router.get("/{investigation_id}/evidence")
async def get_investigation_evidence(
    investigation_id: str = Path(...),
) -> Dict[str, Any]:
    """Retrieves the fused evidence cards and relationship graph."""
    inv = investigation_service.get_investigation(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found.")

    cards = investigation_service.get_evidence(investigation_id)
    res_data = inv.result_data or {}

    return {
        "investigation_id": investigation_id,
        "total_evidence_count": len(cards),
        "evidence_cards": cards,
        "relationships": res_data.get("evidence_relationships", []),
        "clusters": res_data.get("evidence_clusters", []),
        "conflicts": res_data.get("conflicts", []),
    }


@router.get("/{investigation_id}/findings")
async def get_investigation_findings(
    investigation_id: str = Path(...),
) -> Dict[str, Any]:
    """Retrieves empirical findings strictly tied to evidence IDs."""
    findings = investigation_service.get_findings(investigation_id)
    return {
        "investigation_id": investigation_id,
        "findings": findings,
    }


@router.get("/{investigation_id}/timeline")
async def get_investigation_timeline(
    investigation_id: str = Path(...),
) -> Dict[str, Any]:
    """Retrieves multi-temporal milestones and surface transition states."""
    timeline = investigation_service.get_timeline(investigation_id)
    return {
        "investigation_id": investigation_id,
        "milestones": timeline,
    }


@router.get("/{investigation_id}/artifacts")
async def get_investigation_artifacts(
    investigation_id: str = Path(...),
) -> List[Dict[str, Any]]:
    """Returns downloadable report and GIS artifacts for the investigation."""
    artifacts = investigation_service.get_artifacts(investigation_id)
    return [a.dict() for a in artifacts]


@router.get("/{investigation_id}/artifacts/{artifact_type}")
async def download_investigation_artifact(
    investigation_id: str = Path(...),
    artifact_type: str = Path(..., description="report_json, report_html, evidence_geojson, or manifest"),
):
    """Downloads a specific artifact document."""
    inv = investigation_service.get_investigation(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found.")

    target = None
    for art in inv.artifacts:
        if art.artifact_type == artifact_type:
            target = art
            break

    if not target or not os.path.exists(target.file_path):
        raise HTTPException(status_code=404, detail=f"Artifact '{artifact_type}' is not available.")

    return FileResponse(
        path=target.file_path,
        media_type=target.mime_type,
        filename=target.name,
    )


@router.post("/{investigation_id}/cancel")
async def cancel_investigation(
    investigation_id: str = Path(...),
) -> Dict[str, Any]:
    """Requests cancellation of an ongoing investigation."""
    success = investigation_service.cancel_investigation(investigation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    return {"investigation_id": investigation_id, "status": "cancelled"}


# -----------------------------------------------------------------------------
# Analyst Notes Endpoints
# -----------------------------------------------------------------------------

@router.post("/{investigation_id}/notes", status_code=status.HTTP_201_CREATED)
async def create_analyst_note(
    investigation_id: str = Path(...),
    note: AnalystNote = ...,
) -> AnalystNote:
    """Adds a human analyst annotation to an investigation or finding."""
    note.investigation_id = investigation_id
    return investigation_service.add_note(note)


@router.get("/{investigation_id}/notes")
async def get_analyst_notes(
    investigation_id: str = Path(...),
) -> List[Dict[str, Any]]:
    """Returns all annotations attached to an investigation."""
    notes = investigation_service.get_notes(investigation_id)
    return [n.dict() for n in notes]


@router.delete("/{investigation_id}/notes/{note_id}")
async def delete_analyst_note(
    investigation_id: str = Path(...),
    note_id: str = Path(...),
) -> Dict[str, Any]:
    """Deletes an analyst note."""
    success = investigation_service.delete_note(investigation_id, note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found.")
    return {"status": "deleted", "note_id": note_id}
