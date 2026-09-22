"""
TRINETRA Phase 7 — Persistent Intelligence, Semantic Search & Monitoring REST Endpoints
Mounted at /api/v1/explore/...
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Query, Body
from intelligence.models import EventState
from intelligence.schemas import (
    EventResponse,
    EventStateUpdateRequest,
    FindingResponse,
    SearchRequest,
    SearchResponse,
    SimilarityRequest,
    SimilarityResponse,
    RegionalSummaryResponse,
    HotspotResponse,
    AnomalyResponse,
    MonitorCreateRequest,
    MonitorResponse,
    MonitorAlertResponse,
    InvestigationTemplateCreateRequest,
    InvestigationTemplateResponse,
    TemplateRunRequest,
    SavedSearchRequest,
    SavedRegionRequest,
    SplitEventRequest,
    MergeEventsRequest,
)
from intelligence.service import intelligence_service
from intelligence.monitoring.service import monitoring_service
from intelligence.lifecycle import EventLifecycleManager, InvalidLifecycleTransitionError
from intelligence.events.merger import EventMerger
from intelligence.events.splitter import EventSplitter

logger = logging.getLogger("trinetra.intelligence")

router = APIRouter(tags=["intelligence"])


# =====================================================================
# 1. Events Endpoints
# =====================================================================

@router.get("/api/v1/explore/intelligence/events", response_model=List[EventResponse])
def list_events(
    state: Optional[str] = Query(None, description="Filter by event state"),
    semantic_class: Optional[str] = Query(None, description="Filter by semantic category"),
    region_id: Optional[str] = Query(None, description="Filter by canonical region ID"),
    limit: int = Query(50, ge=1, le=100),
):
    events = intelligence_service.repo.list_events(
        state=state,
        semantic_class=semantic_class,
        region_id=region_id,
        limit=limit,
    )
    return [e.to_dict() for e in events]


@router.get("/api/v1/explore/intelligence/events/{event_id}", response_model=EventResponse)
def get_event(event_id: str):
    event = intelligence_service.repo.get_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"EOEvent '{event_id}' not found.",
        )
    return event.to_dict()


@router.patch("/api/v1/explore/intelligence/events/{event_id}/state", response_model=EventResponse)
def update_event_state(event_id: str, request: EventStateUpdateRequest):
    event = intelligence_service.repo.get_event(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"EOEvent '{event_id}' not found.",
        )

    try:
        target_state = EventState(request.new_state)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid event state '{request.new_state}'. Allowed: {[s.value for s in EventState]}",
        )

    try:
        EventLifecycleManager.validate_transition(event.state, target_state)
    except InvalidLifecycleTransitionError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    intelligence_service.repo.update_event_state(
        event_id=event_id,
        new_state=target_state,
        reason=request.reason,
    )

    updated_event = intelligence_service.repo.get_event(event_id)
    return updated_event.to_dict()


@router.post("/api/v1/explore/intelligence/events/{event_id}/split", response_model=List[EventResponse])
def split_event(event_id: str, request: SplitEventRequest):
    parent = intelligence_service.repo.get_event(event_id)
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent EOEvent '{event_id}' not found.",
        )
    children = EventSplitter.split_event(
        parent_event=parent,
        split_definitions=request.child_definitions,
        repository=intelligence_service.repo,
    )
    return [c.to_dict() for c in children]


@router.post("/api/v1/explore/intelligence/events/{event_id}/merge", response_model=EventResponse)
def merge_events(event_id: str, request: MergeEventsRequest):
    primary = intelligence_service.repo.get_event(event_id)
    if not primary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Primary EOEvent '{event_id}' not found.",
        )
    secondary = intelligence_service.repo.get_event(request.secondary_event_id)
    if not secondary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Secondary EOEvent '{request.secondary_event_id}' not found.",
        )
    merged_primary, _ = EventMerger.merge_events(
        primary_event=primary,
        secondary_event=secondary,
        repository=intelligence_service.repo,
    )
    return merged_primary.to_dict()


# =====================================================================
# 2. Findings Endpoints
# =====================================================================

@router.get("/api/v1/explore/intelligence/findings", response_model=List[FindingResponse])
def list_findings(
    investigation_id: Optional[str] = Query(None),
    semantic_class: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
):
    findings = intelligence_service.repo.list_findings(
        investigation_id=investigation_id,
        semantic_class=semantic_class,
        limit=limit,
    )
    return [f.to_dict() for f in findings]


@router.get("/api/v1/explore/intelligence/findings/{finding_id}", response_model=FindingResponse)
def get_finding(finding_id: str):
    finding = intelligence_service.repo.get_finding(finding_id)
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Finding '{finding_id}' not found.",
        )
    return finding.to_dict()


# =====================================================================
# 3. Search & Similarity Endpoints
# =====================================================================

@router.post("/api/v1/explore/intelligence/search", response_model=SearchResponse)
def search_intelligence(request: SearchRequest):
    return intelligence_service.search(request)


@router.post("/api/v1/explore/intelligence/similar", response_model=SimilarityResponse)
def find_similar(request: SimilarityRequest):
    return intelligence_service.find_similar(
        entity_id=request.entity_id,
        entity_type=request.entity_type,
        limit=request.limit,
        threshold=request.threshold,
    )


# =====================================================================
# 4. Regional Intelligence & Hotspots
# =====================================================================

@router.get("/api/v1/explore/intelligence/regions")
def list_regions(limit: int = Query(50, ge=1, le=100)):
    regions = intelligence_service.repo.list_regions(limit=limit)
    return [r.to_dict() for r in regions]


@router.get("/api/v1/explore/intelligence/regions/{region_id}", response_model=RegionalSummaryResponse)
def get_regional_summary(region_id: str):
    summary = intelligence_service.get_regional_summary(region_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Region '{region_id}' not found.",
        )
    return summary


@router.get("/api/v1/explore/intelligence/hotspots", response_model=List[HotspotResponse])
def list_hotspots(min_events: int = Query(2, ge=1, le=10)):
    return intelligence_service.list_hotspots(min_events=min_events)


# =====================================================================
# 5. Anomalies
# =====================================================================

@router.get("/api/v1/explore/intelligence/anomalies", response_model=List[AnomalyResponse])
def list_anomalies(
    status_filter: Optional[str] = Query(None, alias="status"),
    region_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
):
    anomalies = intelligence_service.list_anomalies(
        status=status_filter,
        region_id=region_id,
        limit=limit,
    )
    return [a.to_dict() for a in anomalies]


# =====================================================================
# 6. Continuous Monitoring
# =====================================================================

@router.post("/api/v1/explore/monitoring", response_model=MonitorResponse, status_code=status.HTTP_201_CREATED)
def create_monitor(request: MonitorCreateRequest):
    try:
        m = monitoring_service.create_monitor(
            name=request.name,
            aoi=request.aoi or {},
            bounding_box=request.bounding_box or getattr(request, "bbox", None) or [],
            observation_collection=request.observation_collection,
            schedule_cadence=request.schedule_cadence,
            template_id=request.template_id or "",
            trigger_condition=request.trigger_condition,
            cooldown_hours=request.cooldown_hours,
        )
        return m.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/api/v1/explore/monitoring", response_model=List[MonitorResponse])
def list_monitors(enabled_only: bool = Query(False)):
    monitors = monitoring_service.list_monitors(enabled_only=enabled_only)
    return [m.to_dict() for m in monitors]


@router.get("/api/v1/explore/monitoring/alerts", response_model=List[MonitorAlertResponse])
def list_monitor_alerts(
    monitor_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
):
    alerts = monitoring_service.list_alerts(monitor_id=monitor_id, limit=limit)
    return [a.to_dict() for a in alerts]


@router.post("/api/v1/explore/monitoring/alerts/{alert_id}/acknowledge")
@router.post("/api/v1/explore/monitoring/alerts/{alert_id}/ack")
def acknowledge_monitor_alert(alert_id: str):
    success = intelligence_service.repo.acknowledge_alert(alert_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert '{alert_id}' not found.",
        )
    return {"alert_id": alert_id, "acknowledged": True}


@router.get("/api/v1/explore/monitoring/{monitor_id}", response_model=MonitorResponse)
def get_monitor(monitor_id: str):
    m = monitoring_service.get_monitor(monitor_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Monitor '{monitor_id}' not found.")
    return m.to_dict()


@router.post("/api/v1/explore/monitoring/{monitor_id}/enable")
def enable_monitor(monitor_id: str):
    success = monitoring_service.enable_monitor(monitor_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Monitor '{monitor_id}' not found.")
    return {"monitor_id": monitor_id, "enabled": True}


@router.post("/api/v1/explore/monitoring/{monitor_id}/disable")
def disable_monitor(monitor_id: str):
    success = monitoring_service.disable_monitor(monitor_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Monitor '{monitor_id}' not found.")
    return {"monitor_id": monitor_id, "enabled": False}


@router.delete("/api/v1/explore/monitoring/{monitor_id}")
def delete_monitor(monitor_id: str):
    success = monitoring_service.delete_monitor(monitor_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Monitor '{monitor_id}' not found.")
    return {"monitor_id": monitor_id, "deleted": True}


@router.get("/api/v1/explore/monitoring/{monitor_id}/runs")
def list_monitor_runs(monitor_id: str, limit: int = Query(20, ge=1, le=100)):
    runs = intelligence_service.repo.list_monitor_runs(monitor_id, limit=limit)
    return [r.to_dict() for r in runs]


# =====================================================================
# 7. Saved Searches
# =====================================================================

@router.post("/api/v1/explore/searches", status_code=status.HTTP_201_CREATED)
def save_search(request: SavedSearchRequest):
    import uuid
    sid = f"srch_{uuid.uuid4().hex[:8]}"
    intelligence_service.repo.save_saved_search(
        search_id=sid,
        name=request.name,
        query=request.query,
        filters=request.filters,
    )
    return {"search_id": sid, "name": request.name, "created": True}


@router.get("/api/v1/explore/searches")
def list_saved_searches():
    return intelligence_service.repo.list_saved_searches()


@router.delete("/api/v1/explore/searches/{search_id}")
def delete_saved_search(search_id: str):
    success = intelligence_service.repo.delete_saved_search(search_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Search '{search_id}' not found.")
    return {"search_id": search_id, "deleted": True}


# =====================================================================
# 8. Saved Regions
# =====================================================================

@router.post("/api/v1/explore/saved-regions", status_code=status.HTTP_201_CREATED)
def save_region(request: SavedRegionRequest):
    import uuid
    rid = f"sreg_{uuid.uuid4().hex[:8]}"
    intelligence_service.repo.save_saved_region(
        saved_region_id=rid,
        name=request.name,
        aoi=request.aoi,
        bounding_box=request.bounding_box,
        description=request.description or "",
        tags=request.tags,
    )
    return {"saved_region_id": rid, "name": request.name, "created": True}


@router.get("/api/v1/explore/saved-regions")
def list_saved_regions():
    return intelligence_service.repo.list_saved_regions()


@router.delete("/api/v1/explore/saved-regions/{saved_region_id}")
def delete_saved_region(saved_region_id: str):
    success = intelligence_service.repo.delete_saved_region(saved_region_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Region '{saved_region_id}' not found.")
    return {"saved_region_id": saved_region_id, "deleted": True}


# =====================================================================
# 9. Investigation Templates & Execution
# =====================================================================

@router.post("/api/v1/explore/templates", response_model=InvestigationTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(request: InvestigationTemplateCreateRequest):
    tmpl = intelligence_service.create_template(
        name=request.name,
        question=request.question,
        analysis_mode=request.analysis_mode,
        required_evidence=request.required_evidence,
        time_configuration=request.time_configuration,
        semantic_targets=request.semantic_targets,
        filters=request.filters,
    )
    return tmpl.to_dict()


@router.get("/api/v1/explore/templates", response_model=List[InvestigationTemplateResponse])
def list_templates():
    templates = intelligence_service.repo.list_templates()
    return [t.to_dict() for t in templates]


@router.get("/api/v1/explore/templates/{template_id}", response_model=InvestigationTemplateResponse)
def get_template(template_id: str):
    tmpl = intelligence_service.repo.get_template(template_id)
    if not tmpl:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Template '{template_id}' not found.")
    return tmpl.to_dict()


@router.post("/api/v1/explore/templates/{template_id}/run", status_code=status.HTTP_202_ACCEPTED)
def run_template(template_id: str, request: TemplateRunRequest):
    try:
        res = intelligence_service.run_template(
            template_id=template_id,
            observation_ids=request.observation_ids,
            aoi=request.aoi,
        )
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# =====================================================================
# 10. Intelligence AI Status & Aliases
# =====================================================================

@router.get("/api/v1/explore/intelligence/ai/status")
def get_intelligence_ai_status():
    events = intelligence_service.repo.list_events(limit=1)
    monitors = monitoring_service.list_monitors()
    return {
        "available": True,
        "events_count": len(events),
        "monitors_count": len(monitors),
        "version": "7.0.0",
        "phase": 7,
    }


# Template Aliases
@router.get("/api/v1/explore/intelligence/templates", response_model=List[InvestigationTemplateResponse])
def list_intelligence_templates():
    return list_templates()


@router.post("/api/v1/explore/intelligence/templates", response_model=InvestigationTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_intelligence_template(request: InvestigationTemplateCreateRequest):
    return create_template(request)


# Monitor Aliases
@router.get("/api/v1/explore/intelligence/monitors", response_model=List[MonitorResponse])
def list_intelligence_monitors(enabled_only: bool = Query(False)):
    return list_monitors(enabled_only=enabled_only)


@router.post("/api/v1/explore/intelligence/monitors", response_model=MonitorResponse, status_code=status.HTTP_200_OK)
def create_intelligence_monitor(request: MonitorCreateRequest):
    return create_monitor(request)


@router.post("/api/v1/explore/intelligence/monitors/{monitor_id}/toggle")
def toggle_intelligence_monitor(monitor_id: str):
    m = monitoring_service.get_monitor(monitor_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Monitor '{monitor_id}' not found.")
    new_state = not m.enabled
    if new_state:
        monitoring_service.enable_monitor(monitor_id)
    else:
        monitoring_service.disable_monitor(monitor_id)
    return {"monitor_id": monitor_id, "enabled": new_state}
