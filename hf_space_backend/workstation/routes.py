"""
TRINETRA Workstation — FastAPI Router & REST Endpoints
Implements Section 6 API Contracts matching implementation-plan.md.
"""

import os
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse

from .schemas import (
    Mission,
    AreaOfInterest,
    Asset,
    AnalysisPlan,
    AnalysisRun,
    NotebookEntry,
    PipelineDefinition,
    CreateMissionRequest,
    CreateAOIRequest,
    DraftPlanRequest,
    ValidatePlanRequest,
    ApprovePlanRequest,
    SubmitRunRequest,
    AddNotebookEntryRequest,
)
from .pipeline_registry import list_pipelines, get_pipeline
from .planner import CopilotPlanner
from .service import workstation_service, UPLOAD_BASE_DIR, RUNS_BASE_DIR

router = APIRouter(prefix="/api/v1/workstation", tags=["Workstation"])


# --- Missions ---

@router.get("/missions", response_model=List[Mission])
def list_missions():
    """Returns all authorized missions."""
    return workstation_service.list_missions()


@router.post("/missions", response_model=Mission)
def create_mission(request: CreateMissionRequest):
    """Initializes a new research mission workspace."""
    return workstation_service.create_mission(request)


@router.get("/missions/{mission_id}", response_model=Mission)
def get_mission(mission_id: str):
    m = workstation_service.get_mission(mission_id)
    if not m:
        raise HTTPException(status_code=404, detail="Mission not found")
    return m


# --- Areas of Interest (AOIs) ---

@router.get("/missions/{mission_id}/aois", response_model=List[AreaOfInterest])
def list_aois(mission_id: str):
    return workstation_service.list_aois(mission_id)


@router.post("/missions/{mission_id}/aois", response_model=AreaOfInterest)
def create_aoi(mission_id: str, request: CreateAOIRequest):
    return workstation_service.create_aoi(mission_id, request)


@router.delete("/missions/{mission_id}/aois/{aoi_id}")
def delete_aoi(mission_id: str, aoi_id: str):
    success = workstation_service.delete_aoi(mission_id, aoi_id)
    if not success:
        raise HTTPException(status_code=404, detail="AOI not found")
    return {"success": True, "deleted_id": aoi_id}


# --- Assets & Genuine File Ingestion ---

@router.get("/missions/{mission_id}/assets", response_model=List[Asset])
def list_assets(mission_id: str):
    return workstation_service.list_assets(mission_id)


@router.post("/missions/{mission_id}/assets", response_model=Asset)
def register_asset(mission_id: str, asset: Asset):
    asset.mission_id = mission_id
    return workstation_service.register_asset(mission_id, asset)


@router.delete("/missions/{mission_id}/assets/{asset_id}")
def delete_asset(mission_id: str, asset_id: str):
    success = workstation_service.delete_asset(mission_id, asset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"success": True, "deleted_id": asset_id}


@router.delete("/missions/{mission_id}/collections/{collection_id}")
def delete_collection(mission_id: str, collection_id: str):
    count = workstation_service.delete_collection(mission_id, collection_id)
    return {"success": True, "collection_id": collection_id, "deleted_count": count}



@router.post("/missions/{mission_id}/upload", response_model=Asset)
async def upload_mission_asset(
    mission_id: str,
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    collection_id: Optional[str] = Form(None),
):
    """
    Accepts real uploaded GeoTIFF, COG, or GeoJSON research files,
    streams in 16MB chunks (supporting up to 10 GB bulk uploads),
    parses real headers and metadata, and creates a verified mission asset.
    """
    mission = workstation_service.get_mission(mission_id)
    if not mission:
        all_msns = workstation_service.list_missions()
        if all_msns:
            mission = all_msns[0]
            mission_id = mission.id
        else:
            from .schemas import CreateMissionRequest
            mission = workstation_service.create_mission(
                CreateMissionRequest(name="Primary Research Mission", description="Default mission workspace")
            )
            mission_id = mission.id

    upload_dir = os.path.join(UPLOAD_BASE_DIR, mission_id)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)

    # 16 MB chunked streaming to support large files up to 10 GB in constant memory
    CHUNK_SIZE = 16 * 1024 * 1024
    with open(file_path, "wb") as buffer:
        while True:
            chunk = await file.read(CHUNK_SIZE)
            if not chunk:
                break
            buffer.write(chunk)

    return workstation_service.ingest_uploaded_file(
        mission_id=mission_id,
        saved_file_path=file_path,
        original_filename=file.filename,
        title=title,
        collection_id=collection_id,
    )


@router.get("/missions/{mission_id}/assets/{asset_id}/file")
def get_asset_file(mission_id: str, asset_id: str):
    assets = workstation_service.list_assets(mission_id)
    target = next((a for a in assets if a.id == asset_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Asset not found")
    local_path = target.metadata.get("local_path")
    if not local_path or not os.path.exists(local_path):
        raise HTTPException(status_code=404, detail="Asset file not found on disk")
    return FileResponse(local_path, filename=target.metadata.get("filename", "asset.tif"))


@router.get("/missions/{mission_id}/assets/{asset_id}/preview")
def get_asset_preview(mission_id: str, asset_id: str):
    assets = workstation_service.list_assets(mission_id)
    target = next((a for a in assets if a.id == asset_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Asset not found")
    preview_path = target.metadata.get("preview_path")
    if preview_path and os.path.exists(preview_path):
        return FileResponse(preview_path, media_type="image/png")
    local_path = target.metadata.get("local_path")
    if local_path and os.path.exists(local_path):
        gen_path = os.path.join(os.path.dirname(local_path), f"{asset_id}_preview.png")
        if workstation_service._generate_raster_preview(local_path, gen_path):
            target.metadata["preview_path"] = gen_path
            return FileResponse(gen_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Preview not available")


@router.post("/missions/{mission_id}/catalog/search")
def search_catalog_scenes(
    mission_id: str,
    payload: Dict[str, Any] = None,
):
    """
    Searches real public STAC endpoints for intersecting Copernicus scenes if AOI is defined,
    or returns an empty list. Zero fake mock data.
    """
    payload = payload or {}
    collection = payload.get("collection", "sentinel-2-l2a")
    cloud_max = payload.get("cloudCoverMax", 30)

    aois = workstation_service.list_aois(mission_id)
    if not aois:
        return {"scenes": [], "total_found": 0, "message": "Define an AOI first to discover satellite scenes."}

    target_aoi = aois[0]
    bbox = target_aoi.bbox
    if not bbox or len(bbox) != 4:
        return {"scenes": [], "total_found": 0, "message": "AOI bounding box required for catalog search."}

    # Query real public STAC if network allows
    real_scenes = []
    try:
        import requests
        stac_url = "https://earth-search.aws.element84.com/v1/search"
        req_body = {
            "bbox": bbox,
            "collections": ["sentinel-2-l2a" if "sentinel-2" in collection else "sentinel-1-grd"],
            "limit": 10,
        }
        resp = requests.post(stac_url, json=req_body, timeout=5.0)
        if resp.ok:
            data = resp.json()
            for item in data.get("features", []):
                props = item.get("properties", {})
                cloud = props.get("eo:cloud_cover", 0.0)
                if cloud <= cloud_max:
                    real_scenes.append({
                        "id": item.get("id"),
                        "collection": item.get("collection", collection),
                        "datetime": props.get("datetime", item.get("id")),
                        "cloud_cover": round(float(cloud), 1),
                        "bands": ["B02", "B03", "B04", "B08"],
                        "resolution_m": 10,
                        "provider": "Copernicus / AWS STAC",
                        "thumbnail_url": item.get("assets", {}).get("thumbnail", {}).get("href", ""),
                        "tile_url": item.get("assets", {}).get("visual", {}).get("href", ""),
                        "footprint": item.get("geometry"),
                    })
    except Exception as exc:
        logger.info("Public STAC query skipped or unreachable: %s", exc)

    return {"scenes": real_scenes, "total_found": len(real_scenes)}

    filtered = [s for s in scenes if s.get("cloud_cover", 0) <= cloud_max]
    return {"scenes": filtered, "total_found": len(filtered)}


# --- Pipelines ---

@router.get("/pipelines", response_model=List[PipelineDefinition])
def get_pipelines():
    """Lists versioned analytical pipelines from the declarative registry."""
    return list_pipelines()


# --- Copilot Planning & Human Approval Gate ---

@router.post("/missions/{mission_id}/plan", response_model=AnalysisPlan)
async def draft_analysis_plan(mission_id: str, request: DraftPlanRequest):
    """
    Translates a researcher question into a strictly typed, inspectable AnalysisPlan.
    Does NOT execute any code or worker actions.
    """
    try:
        assets = [a.dict() for a in workstation_service.list_assets(mission_id)]
        aois = [a.dict() for a in workstation_service.list_aois(mission_id)]

        plan = await CopilotPlanner.draft_plan(
            question=request.question,
            mission_id=mission_id,
            aoi_id=request.aoi_id,
            available_assets=assets,
            available_aois=aois,
            user_override_pipeline=request.pipeline_key,
            context_options=request.context_options,
        )
        workstation_service.save_plan(plan)
        return plan
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Failed to draft analysis plan: %s", e)
        raise HTTPException(status_code=500, detail=f"Plan synthesis error: {str(e)}")


@router.post("/plans/{plan_id}/validate", response_model=AnalysisPlan)
def validate_plan(plan_id: str, req: ValidatePlanRequest):
    """Runs rigorous domain and scientific validation against mission parameters."""
    return workstation_service.validate_plan(req.plan)


@router.post("/plans/{plan_id}/approve", response_model=AnalysisPlan)
def approve_plan(plan_id: str, req: ApprovePlanRequest = None):
    """
    The distinct Human Approval Gate.
    Authorizes the plan for execution.
    """
    approved_by = req.approved_by if req else "analyst"
    try:
        approved = workstation_service.approve_plan(plan_id, approved_by=approved_by)
        if not approved:
            raise HTTPException(status_code=404, detail="Plan not found")
        return approved
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))


@router.get("/plans/{plan_id}", response_model=AnalysisPlan)
def get_plan(plan_id: str):
    plan = workstation_service.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


# --- Execution Runs ---

@router.get("/missions/{mission_id}/runs", response_model=List[AnalysisRun])
def list_runs(mission_id: str):
    return workstation_service.list_runs(mission_id)


@router.post("/missions/{mission_id}/runs", response_model=AnalysisRun)
async def submit_run(mission_id: str, request: SubmitRunRequest):
    """
    Submits an approved plan for versioned asynchronous pipeline execution.
    """
    try:
        return await workstation_service.submit_run(mission_id, request.plan_id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.get("/runs/{run_id}", response_model=AnalysisRun)
def get_run(run_id: str):
    run = workstation_service.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/runs/{run_id}/outputs/raster")
def get_run_raster_output(run_id: str):
    """
    Streams the genuine Analysis Ready Data (ARD) GeoTIFF difference raster
    produced by the scientific execution engine for this run.
    """
    run_dir = os.path.join(RUNS_BASE_DIR, run_id)
    tif_path = os.path.join(run_dir, f"change_diff_{run_id}.tif")
    if not os.path.exists(tif_path):
        raise HTTPException(status_code=404, detail="Change difference raster not found for this run")
    return FileResponse(
        path=tif_path,
        media_type="image/tiff",
        filename=f"trinetra_change_{run_id}.tif",
    )


# --- Notebook & Reproducible Exports ---

@router.get("/missions/{mission_id}/notebook", response_model=List[NotebookEntry])
def list_notebook_entries(mission_id: str):
    return workstation_service.list_notebook_entries(mission_id)


@router.post("/missions/{mission_id}/notebook", response_model=NotebookEntry)
def add_notebook_entry(mission_id: str, req: AddNotebookEntryRequest):
    return workstation_service.add_notebook_entry(
        mission_id=mission_id,
        title=req.title,
        body=req.body,
        entry_type=req.entry_type,
        run_id=req.run_id,
        findings_data=req.findings_data,
    )


@router.get("/missions/{mission_id}/export")
def export_mission_package(mission_id: str):
    """
    Generates a full reproducible research package manifest with SHA256 integrity,
    complete run provenance, inputs, parameters, and findings.
    """
    return workstation_service.generate_export_manifest(mission_id)
