"""
TRINETRA Phase 6 — Investigation Domain Models
Core entities representing investigations, sessions, progress, and analyst notes.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, Field


class InvestigationStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InvestigationProgressStage(str, Enum):
    PLANNING = "planning"
    SPECIALISTS = "specialists"
    FUSION = "fusion"
    SEMANTICS = "semantics"
    TRAJECTORY = "trajectory"
    REASONING = "reasoning"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InvestigationProgress(BaseModel):
    current_stage: InvestigationProgressStage = InvestigationProgressStage.PLANNING
    percent: int = Field(0, ge=0, le=100)
    message: str = "Investigation initialized"
    step_index: int = 0
    total_steps: int = 6
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class InvestigationArtifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: f"art_{uuid.uuid4().hex[:10]}")
    name: str
    artifact_type: str
    file_path: str
    mime_type: str
    size_bytes: Optional[int] = None
    download_url: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AnalystNote(BaseModel):
    note_id: str = Field(default_factory=lambda: f"note_{uuid.uuid4().hex[:10]}")
    investigation_id: str
    text: str
    attachment_type: Optional[str] = None  # "finding", "observation", "region", "object"
    attachment_id: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Investigation(BaseModel):
    """
    First-class Investigation object representing an integrated, multi-specialist EO enquiry.
    """
    investigation_id: str = Field(default_factory=lambda: f"inv_{uuid.uuid4().hex[:10]}")
    question: str
    aoi: Optional[Dict[str, Any]] = None
    observation_ids: List[str] = Field(default_factory=list)
    temporal_scope: Dict[str, Any] = Field(default_factory=dict)
    intent: str = "GENERAL_CHANGE"
    required_evidence: List[str] = Field(default_factory=list)
    status: InvestigationStatus = InvestigationStatus.QUEUED
    progress: InvestigationProgress = Field(default_factory=InvestigationProgress)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    artifacts: List[InvestigationArtifact] = Field(default_factory=list)
    result_data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    cancel_requested: bool = False
