"""
SatQuery AI — FastAPI Backend Server
SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)
Exposes REST endpoints for multimodal remote-sensing analysis, job tracking,
observability trace inspection, and report downloading.
"""

import os
import sys
import uuid
import shutil
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

# Add backend and project root to sys.path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, PROJECT_ROOT)

from agent.controller import AgentController
from agent.registry import list_tools
from models.loader import ModelRegistryStatus
from services.llm_engine import LLMReasoningEngine
from llm.model_registry import local_registry
from observability.langfuse_tracer import LangfuseTracer
from qml.config import qml_config
from qml.backends.simulator import get_quantum_backend

app = FastAPI(
    title="SatQuery AI — Vision-Language Assistant API",
    version="2.0.0",
    description="100% Local Agentic Remote-Sensing Intelligence Platform for Multimodal Satellite Analysis"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(BACKEND_DIR, "uploads")
REPORTS_DIR = os.path.join(BACKEND_DIR, "outputs", "reports")
SAMPLES_DIR = os.path.join(BACKEND_DIR, "sample_data")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Mount static directories
app.mount("/static/samples", StaticFiles(directory=SAMPLES_DIR), name="samples")
if os.path.exists(REPORTS_DIR):
    app.mount("/static/reports", StaticFiles(directory=REPORTS_DIR), name="reports")

# In-memory job repository
JOBS_DB = {}
controller = AgentController()

@app.on_event("startup")
def startup_diagnostics():
    print("=" * 60)
    print(" SATQUERY AI — 100% LOCAL AGENTIC PLATFORM INITIALIZED")
    print(" Agent Framework : LangChain (langchain-ollama)")
    print(f" LLM Runtime    : Ollama ({local_registry.get_ollama_host()})")
    print(f" Ollama Online  : {local_registry.is_ollama_online()}")
    print(f" Local Models   : {local_registry.probe_installed_models()}")
    print(f" Telemetry      : Langfuse (Enabled={LangfuseTracer.is_available()})")
    print(" Cloud LLM      : NONE (100% Air-Gapped / Zero External APIs)")
    print("=" * 60)

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SatQuery AI Backend",
        "version": "2.0.0",
        "agent_framework": "LangChain",
        "cloud_llm": False,
        "ollama": {
            "connected": local_registry.is_ollama_online(),
            "host": local_registry.get_ollama_host(),
            "models": local_registry.probe_installed_models()
        },
        "langfuse": {
            "connected": LangfuseTracer.is_available(),
            "host": os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")
        },
        "models_status": ModelRegistryStatus.get_status(),
        "llm_status": local_registry.get_status_summary(),
        "qml_status": {
            "enabled": qml_config.enabled,
            "device": qml_config.device_name,
            "qubits": qml_config.num_qubits,
            "layers": qml_config.num_layers
        }
    }

@app.get("/api/v1/qml/status")
def get_qml_status():
    backend = get_quantum_backend()
    return {
        "enabled": qml_config.enabled,
        "mode": qml_config.mode,
        "device": qml_config.device_name,
        "qubits": qml_config.num_qubits,
        "layers": qml_config.num_layers,
        "supported_tasks": qml_config.supported_tasks,
        "telemetry": backend.get_telemetry()
    }

@app.get("/api/v1/llm-status")
def get_llm_status():
    return local_registry.get_status_summary()

@app.get("/api/v1/registry")
def get_tool_registry():
    return {
        "tools": list_tools(),
        "checkpoint_status": ModelRegistryStatus.get_status(),
        "llm_status": local_registry.get_status_summary(),
        "qml_enabled": qml_config.enabled
    }

@app.get("/api/v1/samples")
def get_demo_samples():
    """Provides preset demonstration datasets and recommended queries for evaluation."""
    return [
        {
            "id": "single_optical_vqa",
            "title": "Single Optical VQA (Land-Cover & Water)",
            "mode": "single",
            "files": ["/static/samples/sample_optical.tif"],
            "query": "What are the predominant land-cover types and is there any water body present?",
            "expected_task": "vqa",
            "description": "Analyzes optical multi-spectral reflectance, vegetation cover, and surface hydrology."
        },
        {
            "id": "single_optical_grounding",
            "title": "Single Optical Text-Guided Grounding",
            "mode": "single",
            "files": ["/static/samples/sample_optical.tif"],
            "query": "Highlight the water body referred to in the query",
            "expected_task": "grounding",
            "description": "Locates hydrological contours and draws tactical bounding box overlays."
        },
        {
            "id": "single_scene_caption",
            "title": "Single Image Scene Description",
            "mode": "single",
            "files": ["/static/samples/sample_optical.tif"],
            "query": "Describe the land-cover and major objects visible in this image.",
            "expected_task": "captioning",
            "description": "Generates rich scene description and Corine-style land-cover statistics."
        },
        {
            "id": "bitemporal_change",
            "title": "Bi-Temporal Urban Change Analysis",
            "mode": "bi_temporal",
            "files": ["/static/samples/sample_t1.tif", "/static/samples/sample_t2.tif"],
            "query": "What changed between these two dates, and where did the change occur?",
            "expected_task": "change_analysis",
            "description": "Differential feature comparison detecting urban expansion and generating a change heatmap."
        },
        {
            "id": "optical_sar_joint",
            "title": "Optical–SAR Cross-Modal Fusion",
            "mode": "optical_sar",
            "files": ["/static/samples/sample_opt_pair.tif", "/static/samples/sample_sar_pair.tif"],
            "query": "Use the optical and SAR images together to identify built-up and water-covered regions.",
            "expected_task": "optical_sar_fusion",
            "description": "Combines optical spectral reflectance with SAR microwave backscatter to resolve structures."
        }
    ]

@app.post("/api/v1/analyze")
async def analyze_request(
    files: List[UploadFile] = File(...),
    query: str = Form(...),
    input_mode: str = Form("single"),
    modalities: Optional[str] = Form(None),
    response_language: Optional[str] = Form("en")
):
    request_id = str(uuid.uuid4())
    req_upload_dir = os.path.join(UPLOAD_DIR, request_id)
    os.makedirs(req_upload_dir, exist_ok=True)

    saved_paths = []
    try:
        for f in files:
            dest_path = os.path.join(req_upload_dir, f.filename)
            with open(dest_path, "wb") as buffer:
                shutil.copyfileobj(f.file, buffer)
            saved_paths.append(dest_path)

        declared_mods = [m.strip() for m in modalities.split(",")] if modalities else None

        # Execute through master agent controller
        result_payload = controller.process_request(
            file_paths=saved_paths,
            query=query,
            input_mode=input_mode,
            declared_modalities=declared_mods,
            response_language=response_language or "en"
        )

        JOBS_DB[result_payload["request_id"]] = result_payload
        return result_payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/analyze-preset")
async def analyze_preset(
    sample_id: str = Form(...),
    response_language: Optional[str] = Form("en")
):
    """Executes a preloaded sample scenario without needing re-upload."""
    samples = {s["id"]: s for s in get_demo_samples()}
    if sample_id not in samples:
        raise HTTPException(status_code=404, detail="Sample scenario not found.")

    preset = samples[sample_id]
    local_paths = []
    for rel_path in preset["files"]:
        filename = os.path.basename(rel_path)
        full_path = os.path.join(SAMPLES_DIR, filename)
        if not os.path.exists(full_path):
            raise HTTPException(status_code=500, detail=f"Sample file {filename} not found.")
        local_paths.append(full_path)

    try:
        result_payload = controller.process_request(
            file_paths=local_paths,
            query=preset["query"],
            input_mode=preset["mode"],
            response_language=response_language or "en"
        )
        JOBS_DB[result_payload["request_id"]] = result_payload
        return result_payload
    except Exception as e:
        print(f"[AnalyzePreset] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/jobs/{request_id}")
def get_job_status(request_id: str):
    if request_id not in JOBS_DB:
        raise HTTPException(status_code=404, detail="Job request not found.")
    job = JOBS_DB[request_id]
    return {
        "request_id": request_id,
        "status": job.get("status", "completed"),
        "task": job.get("task")
    }

@app.get("/api/v1/results/{request_id}")
def get_job_result(request_id: str):
    if request_id not in JOBS_DB:
        raise HTTPException(status_code=404, detail="Job result not found.")
    return JOBS_DB[request_id]

@app.get("/api/v1/reports/{request_id}/html")
def get_html_report(request_id: str):
    filename = f"report_{request_id[:8]}.html"
    filepath = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report file not found.")
    return FileResponse(filepath, media_type="text/html", filename=filename)

@app.get("/api/v1/reports/{request_id}/json")
def get_json_report(request_id: str):
    filename = f"report_{request_id[:8]}.json"
    filepath = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="JSON Report file not found.")
    return FileResponse(filepath, media_type="application/json", filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
