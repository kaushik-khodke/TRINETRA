"""
SatQuery AI — Observable Execution Trace System
Provides an auditable, transparent record of task classification,
specialist tool selection, permitted parameters, and pipeline execution.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class TraceStep(BaseModel):
    step_id: int
    stage: str
    action: str
    tool: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: str = "success"  # "success", "warning", "error"
    timestamp_ms: float = Field(default_factory=lambda: time.time() * 1000)
    details: str

class ExecutionTrace(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: Optional[str] = None
    langfuse_url: Optional[str] = None
    llm_model: Optional[str] = None
    agent_framework: str = "langchain"
    input_mode: str
    query: str
    detected_task: str
    selected_tools: List[Dict[str, str]] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    steps: List[TraceStep] = Field(default_factory=list)
    status: str = "initialized"
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None

    def add_step(self, stage: str, action: str, tool: Optional[str] = None, 
                 parameters: Optional[Dict[str, Any]] = None, details: str = "", status: str = "success") -> None:
        step_id = len(self.steps) + 1
        step = TraceStep(
            step_id=step_id,
            stage=stage,
            action=action,
            tool=tool,
            parameters=parameters or {},
            status=status,
            details=details
        )
        self.steps.append(step)

    def complete(self, status: str = "completed") -> None:
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000, 2)
        self.status = status

    def fail(self, error_message: str) -> None:
        self.add_step(
            stage="error",
            action="pipeline_halted",
            status="error",
            details=error_message
        )
        self.complete(status="failed")
