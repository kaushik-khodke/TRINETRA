"""
TRINETRA Analysis Engine — Execution Models
Defines internal job representations, lifecycle statuses, progress stages, and artifacts.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import uuid


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisProgressStage(str, Enum):
    VALIDATING = "validating"
    RESOLVING_ASSETS = "resolving_assets"
    PREPROCESSING = "preprocessing"
    INFERENCE = "inference"
    EVIDENCE = "evidence"
    REASONING = "reasoning"
    REPORT = "report"


class AnalysisProgress(BaseModel):
    stage: AnalysisProgressStage = Field(default=AnalysisProgressStage.VALIDATING)
    message: str = Field(default="Initializing analysis pipeline...")
    step_number: int = Field(default=1, description="Current stage index (1-7)")
    step_index: int = Field(default=1, description="Current stage index (1-7)")
    total_steps: int = Field(default=7, description="Total stages in pipeline")
    percent: int = Field(default=0, description="Completion percentage (0-100)")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AnalysisArtifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: f"art_{uuid.uuid4().hex[:8]}")
    name: str
    artifact_type: str = Field(description="geotiff | geojson | png | json | pdf")
    file_path: str
    relative_url: str
    file_size_bytes: int = 0
    description: Optional[str] = None


class AnalysisRun(BaseModel):
    run_id: str = Field(default_factory=lambda: f"run_{uuid.uuid4().hex[:10]}")
    request_id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}")
    status: RunStatus = Field(default=RunStatus.QUEUED)
    mode: str = Field(default="BI_TEMPORAL")
    query: str = Field(default="")
    aoi_hash: Optional[str] = None
    observation_ids: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: AnalysisProgress = Field(default_factory=AnalysisProgress)
    artifacts: List[AnalysisArtifact] = Field(default_factory=list)
    result_data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    cancel_requested: bool = False
