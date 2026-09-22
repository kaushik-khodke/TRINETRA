"""
TRINETRA Phase 8 — Analyst Workspace REST Router
Mounted at /api/v1/workspace/...
"""

import logging
import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Query, Body, Response
from fastapi.responses import HTMLResponse, FileResponse

try:
    from backend.workspace.service import WorkspaceService
    from backend.workspace.models import (
        WorkspaceStatus,
        ReviewStatus,
        TaskPriority,
        PlanStepType,
        InvestigationStep,
        ReportClaim,
        ReportSection,
    )
    from backend.workspace.schemas import (
        WorkspaceCreateRequest,
        WorkspaceUpdateRequest,
        WorkspaceResponse,
        WorkspaceContextResponse,
        WorkspaceActivityResponse,
        InvestigationPlanCreateRequest,
        InvestigationPlanResponse,
        InvestigationPlanRunResponse,
        RegionComparisonRequest,
        RegionComparisonResponse,
        BatchJobCreateRequest,
        BatchJobResponse,
        EvidenceBoardItemCreateRequest,
        EvidenceBoardItemResponse,
        EvidenceBoardRelationCreateRequest,
        EvidenceBoardRelationResponse,
        AnnotationCreateRequest,
        AnnotationResponse,
        ReviewRecordCreateRequest,
        ReviewRecordResponse,
        FollowUpCreateRequest,
        FollowUpResponse,
        ReportDocumentCreateRequest,
        ReportDocumentResponse,
        WorkspaceTaskCreateRequest,
        WorkspaceTaskResponse,
        WorkspaceSnapshotResponse,
    )
except ImportError:
    from workspace.service import WorkspaceService
    from workspace.models import (
        WorkspaceStatus,
        ReviewStatus,
        TaskPriority,
        PlanStepType,
        InvestigationStep,
        ReportClaim,
        ReportSection,
    )
    from workspace.schemas import (
        WorkspaceCreateRequest,
        WorkspaceUpdateRequest,
        WorkspaceResponse,
        WorkspaceContextResponse,
        WorkspaceActivityResponse,
        InvestigationPlanCreateRequest,
        InvestigationPlanResponse,
        InvestigationPlanRunResponse,
        RegionComparisonRequest,
        RegionComparisonResponse,
        BatchJobCreateRequest,
        BatchJobResponse,
        EvidenceBoardItemCreateRequest,
        EvidenceBoardItemResponse,
        EvidenceBoardRelationCreateRequest,
        EvidenceBoardRelationResponse,
        AnnotationCreateRequest,
        AnnotationResponse,
        ReviewRecordCreateRequest,
        ReviewRecordResponse,
        FollowUpCreateRequest,
        FollowUpResponse,
        ReportDocumentCreateRequest,
        ReportDocumentResponse,
        WorkspaceTaskCreateRequest,
        WorkspaceTaskResponse,
        WorkspaceSnapshotResponse,
    )

logger = logging.getLogger("trinetra.workspace")

router = APIRouter(prefix="/api/v1/workspace", tags=["workspace"])

# Singleton service instance
workspace_service = WorkspaceService()


# =============================================================================
# 1. Workspace Core Endpoints
# =============================================================================

@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(req: WorkspaceCreateRequest):
    try:
        ws = workspace_service.create_workspace(
            name=req.name,
            description=req.description or "",
            current_aoi=req.current_aoi or {},
        )
        return ws.to_dict()
    except Exception as e:
        logger.error("Failed to create workspace: %s", str(e), exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[WorkspaceResponse])
def list_workspaces(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    workspaces = workspace_service.list_workspaces(status=status_filter, limit=limit, offset=offset)
    return [w.to_dict() for w in workspaces]


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(workspace_id: str):
    ws = workspace_service.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' not found.")
    return ws.to_dict()


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(workspace_id: str, req: WorkspaceUpdateRequest):
    try:
        ws = workspace_service.update_workspace(
            workspace_id=workspace_id,
            name=req.name,
            description=req.description,
            current_aoi=req.current_aoi,
            status=req.status,
        )
        return ws.to_dict()
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error("Failed to update workspace '%s': %s", workspace_id, str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{workspace_id}")
def delete_workspace(workspace_id: str):
    deleted = workspace_service.delete_workspace(workspace_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Workspace '{workspace_id}' not found.")
    return {"deleted": True, "workspace_id": workspace_id}


# =============================================================================
# 2. Context & Activity Endpoints
# =============================================================================

@router.get("/{workspace_id}/context", response_model=WorkspaceContextResponse)
def get_workspace_context(workspace_id: str):
    ctx = workspace_service.get_context(workspace_id)
    if not ctx:
        raise HTTPException(status_code=404, detail=f"Context for workspace '{workspace_id}' not found.")
    return ctx.to_dict()


@router.patch("/{workspace_id}/context", response_model=WorkspaceContextResponse)
def update_workspace_context(workspace_id: str, payload: Dict[str, Any] = Body(...)):
    try:
        ctx = workspace_service.update_context(
            workspace_id=workspace_id,
            aoi=payload.get("current_aoi"),
            region_ids=payload.get("active_regions"),
            observation_ids=payload.get("selected_observations"),
            event_ids=payload.get("selected_events"),
            finding_ids=payload.get("selected_findings"),
            open_investigation_id=payload.get("open_investigation_id"),
            active_comparison_id=payload.get("active_comparison_id"),
            active_report_id=payload.get("active_report_id"),
        )
        return ctx.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workspace_id}/activities", response_model=List[WorkspaceActivityResponse])
def list_workspace_activities(
    workspace_id: str,
    activity_type: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    acts = workspace_service.list_activities(
        workspace_id=workspace_id,
        limit=limit,
        offset=offset,
        activity_type=activity_type,
        entity_type=entity_type,
    )
    return [a.to_dict() for a in acts]


# =============================================================================
# 3. Evidence Board Endpoints
# =============================================================================

@router.get("/{workspace_id}/board/items", response_model=List[EvidenceBoardItemResponse])
def list_board_items(workspace_id: str):
    items = workspace_service.list_board_items(workspace_id)
    return [i.to_dict() for i in items]


@router.post("/{workspace_id}/board/items", response_model=EvidenceBoardItemResponse)
def pin_board_item(workspace_id: str, req: EvidenceBoardItemCreateRequest):
    item = workspace_service.pin_item(
        workspace_id=workspace_id,
        item_type=req.type,
        source_id=req.source_id,
        position=req.position,
        title=req.title,
        annotation=req.annotation,
    )
    return item.to_dict()


@router.delete("/{workspace_id}/board/items/{item_id}")
def delete_board_item(workspace_id: str, item_id: str):
    workspace_service.delete_board_item(item_id)
    return {"deleted": True, "item_id": item_id}


@router.get("/{workspace_id}/board/relations", response_model=List[EvidenceBoardRelationResponse])
def list_board_relations(workspace_id: str):
    rels = workspace_service.list_board_relations(workspace_id)
    return [r.to_dict() for r in rels]


@router.post("/{workspace_id}/board/relations", response_model=EvidenceBoardRelationResponse)
def link_board_items(workspace_id: str, req: EvidenceBoardRelationCreateRequest):
    rel = workspace_service.link_items(
        workspace_id=workspace_id,
        source_item_id=req.source_item_id,
        target_item_id=req.target_item_id,
        relation_type=req.relation_type,
        metadata=req.metadata,
    )
    return rel.to_dict()


@router.delete("/{workspace_id}/board/relations/{relation_id}")
def delete_board_relation(workspace_id: str, relation_id: str):
    workspace_service.delete_board_relation(relation_id)
    return {"deleted": True, "relation_id": relation_id}


# =============================================================================
# 4. Investigation Plans & DAG Runs
# =============================================================================

@router.get("/{workspace_id}/plans", response_model=List[InvestigationPlanResponse])
def list_plans(workspace_id: str):
    plans = workspace_service.list_plans(workspace_id)
    return [p.to_dict() for p in plans]


@router.post("/{workspace_id}/plans", response_model=InvestigationPlanResponse)
def create_plan(workspace_id: str, req: InvestigationPlanCreateRequest):
    try:
        steps = [
            InvestigationStep(
                step_id=s.step_id,
                type=PlanStepType(s.type),
                depends_on=s.depends_on,
                parameters=s.parameters,
            )
            for s in req.steps
        ]
        plan = workspace_service.create_plan(
            workspace_id=workspace_id,
            title=req.title,
            question=req.question,
            steps=steps,
            constraints=req.constraints,
            required_evidence=req.required_evidence,
        )
        return plan.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workspace_id}/plans/{plan_id}", response_model=InvestigationPlanResponse)
def get_plan(workspace_id: str, plan_id: str):
    plan = workspace_service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan '{plan_id}' not found.")
    return plan.to_dict()


@router.post("/{workspace_id}/plans/{plan_id}/execute", response_model=InvestigationPlanRunResponse)
def execute_plan(workspace_id: str, plan_id: str, payload: Dict[str, Any] = Body(default_factory=dict)):
    try:
        run = workspace_service.execute_plan(plan_id, execution_context=payload)
        return run.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workspace_id}/plans/{plan_id}/runs", response_model=List[InvestigationPlanRunResponse])
def list_plan_runs(workspace_id: str, plan_id: str):
    runs = workspace_service.list_plan_runs(plan_id)
    return [r.to_dict() for r in runs]


# =============================================================================
# 5. Comparison & Sensitivity Analysis
# =============================================================================

@router.post("/{workspace_id}/compare/regions", response_model=RegionComparisonResponse)
def compare_regions(workspace_id: str, req: RegionComparisonRequest):
    try:
        comp = workspace_service.compare_regions(
            workspace_id=workspace_id,
            region_a_id=req.region_a_id,
            region_b_id=req.region_b_id,
            period=req.period,
            thresholds=req.thresholds,
        )
        return comp.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workspace_id}/compare/regions", response_model=List[RegionComparisonResponse])
def list_comparisons(workspace_id: str):
    comps = workspace_service.list_comparisons(workspace_id)
    return [c.to_dict() for c in comps]


@router.post("/{workspace_id}/compare/events")
def compare_events(workspace_id: str, event_ids: List[str] = Body(..., embed=True)):
    try:
        res = workspace_service.compare_events(workspace_id, event_ids)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# 6. Batch Processing
# =============================================================================

@router.post("/{workspace_id}/batch", response_model=BatchJobResponse)
def execute_batch_job(workspace_id: str, req: BatchJobCreateRequest):
    try:
        targets_dicts = [t.model_dump() for t in req.targets]
        job = workspace_service.execute_batch(
            workspace_id=workspace_id,
            template_id=req.template_id,
            targets=targets_dicts,
            concurrency=req.concurrency,
        )
        return job.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workspace_id}/batch", response_model=List[BatchJobResponse])
def list_batch_jobs(workspace_id: str):
    jobs = workspace_service.list_batch_jobs(workspace_id)
    return [j.to_dict() for j in jobs]


@router.get("/{workspace_id}/batch/{batch_id}", response_model=BatchJobResponse)
def get_batch_job(workspace_id: str, batch_id: str):
    job = workspace_service.get_batch_job(batch_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Batch job '{batch_id}' not found.")
    return job.to_dict()


# =============================================================================
# 7. Synthesis & Conflicts
# =============================================================================

@router.post("/{workspace_id}/synthesis")
def generate_synthesis(workspace_id: str):
    try:
        return workspace_service.generate_synthesis(workspace_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# 8. Annotations, Reviews & Follow-ups
# =============================================================================

@router.get("/{workspace_id}/annotations", response_model=List[AnnotationResponse])
def list_annotations(workspace_id: str):
    anns = workspace_service.list_annotations(workspace_id)
    return [a.to_dict() for a in anns]


@router.post("/{workspace_id}/annotations", response_model=AnnotationResponse)
def add_annotation(workspace_id: str, req: AnnotationCreateRequest):
    try:
        ann = workspace_service.add_annotation(
            workspace_id=workspace_id,
            text=req.text,
            type=req.type,
            geometry=req.geometry,
            linked_entity_type=req.linked_entity_type,
            linked_entity_id=req.linked_entity_id,
        )
        return ann.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{workspace_id}/annotations/{annotation_id}")
def delete_annotation(workspace_id: str, annotation_id: str):
    workspace_service.delete_annotation(annotation_id)
    return {"deleted": True, "annotation_id": annotation_id}


@router.get("/{workspace_id}/reviews", response_model=List[ReviewRecordResponse])
def list_reviews(workspace_id: str):
    revs = workspace_service.list_reviews(workspace_id)
    return [r.to_dict() for r in revs]


@router.post("/{workspace_id}/reviews", response_model=ReviewRecordResponse)
def set_review_status(workspace_id: str, req: ReviewRecordCreateRequest):
    try:
        rev = workspace_service.set_review_status(
            workspace_id=workspace_id,
            entity_type=req.entity_type,
            entity_id=req.entity_id,
            status=ReviewStatus(req.status),
            review_note=req.review_note or "",
            analyst_id=req.analyst_id or "analyst",
        )
        return rev.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workspace_id}/follow-ups", response_model=List[FollowUpResponse])
def list_follow_ups(workspace_id: str, status_filter: Optional[str] = Query(None, alias="status")):
    fus = workspace_service.list_follow_ups(workspace_id, status=status_filter)
    return [f.to_dict() for f in fus]


@router.post("/{workspace_id}/follow-ups", response_model=FollowUpResponse)
def create_follow_up(workspace_id: str, req: FollowUpCreateRequest):
    try:
        fu = workspace_service.create_follow_up(
            workspace_id=workspace_id,
            linked_entity_type=req.linked_entity_type,
            linked_entity_id=req.linked_entity_id,
            note=req.note,
            status=req.status or "OPEN",
        )
        return fu.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# 9. Reports & Evidence Packages
# =============================================================================

@router.get("/{workspace_id}/reports", response_model=List[ReportDocumentResponse])
def list_reports(workspace_id: str):
    reports = workspace_service.list_reports(workspace_id)
    return [r.to_dict() for r in reports]


@router.post("/{workspace_id}/reports", response_model=ReportDocumentResponse)
def create_report(workspace_id: str, req: ReportDocumentCreateRequest):
    try:
        sections = []
        for s in req.sections:
            claims = [
                ReportClaim(
                    claim_id=c.claim_id,
                    text=c.text,
                    evidence_ids=c.evidence_ids,
                    type=c.type,
                )
                for c in s.claims
            ]
            sections.append(
                ReportSection(
                    section_id=s.section_id,
                    type=s.type,
                    title=s.title,
                    content=s.content or "",
                    source_ids=s.source_ids,
                    claims=claims,
                    author_type=s.author_type,
                )
            )
        rep = workspace_service.create_report(
            workspace_id=workspace_id,
            title=req.title,
            sections=sections,
            strict_claims=True,
        )
        return rep.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workspace_id}/reports/{report_id}", response_model=ReportDocumentResponse)
def get_report(workspace_id: str, report_id: str):
    rep = workspace_service.get_report(report_id)
    if not rep:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found.")
    return rep.to_dict()


@router.get("/{workspace_id}/reports/{report_id}/render", response_class=HTMLResponse)
def render_report_html(workspace_id: str, report_id: str):
    try:
        html_text = workspace_service.render_report_html(report_id)
        return HTMLResponse(content=html_text, status_code=200)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{workspace_id}/reports/{report_id}/export")
def export_report_package(workspace_id: str, report_id: str):
    try:
        zip_path = workspace_service.export_report_package(report_id)
        return {"exported": True, "package_path": zip_path, "filename": os.path.basename(zip_path)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# 10. Workspace Task Queue
# =============================================================================

@router.post("/{workspace_id}/tasks", response_model=WorkspaceTaskResponse)
def submit_task(workspace_id: str, req: WorkspaceTaskCreateRequest):
    try:
        t = workspace_service.submit_task(
            workspace_id=workspace_id,
            type=req.type,
            priority=TaskPriority(req.priority),
            parameters=req.parameters,
            idempotency_key=req.idempotency_key,
        )
        return t.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workspace_id}/tasks", response_model=List[WorkspaceTaskResponse])
def list_tasks(
    workspace_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    tasks = workspace_service.list_tasks(workspace_id, status=status_filter, limit=limit, offset=offset)
    return [t.to_dict() for t in tasks]


@router.get("/{workspace_id}/tasks/{task_id}", response_model=WorkspaceTaskResponse)
def get_task(workspace_id: str, task_id: str):
    t = workspace_service.get_task(task_id)
    if not t:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return t.to_dict()


@router.post("/{workspace_id}/tasks/{task_id}/cancel")
def cancel_task(workspace_id: str, task_id: str):
    success = workspace_service.cancel_task(task_id)
    return {"cancelled": success, "task_id": task_id}


# =============================================================================
# 11. Snapshots
# =============================================================================

@router.post("/{workspace_id}/snapshots", response_model=WorkspaceSnapshotResponse)
def create_snapshot(workspace_id: str, payload: Dict[str, Any] = Body(default_factory=dict)):
    snap = workspace_service.create_snapshot(workspace_id, state=payload.get("state"))
    return snap.to_dict()


@router.get("/{workspace_id}/snapshots", response_model=List[WorkspaceSnapshotResponse])
def list_snapshots(workspace_id: str):
    snaps = workspace_service.list_snapshots(workspace_id)
    return [s.to_dict() for s in snaps]
