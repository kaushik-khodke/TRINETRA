"""
SatQuery AI — Local LLM & Planning Schemas
Pydantic data models for structured model registry entries, query intent planning,
and multi-step agent execution plans.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

ModelRole = Literal["planner", "fast_router", "lightweight"]

class ModelSpec(BaseModel):
    role: ModelRole
    default_model: str
    description: str
    context_window: int = 8192
    temperature: float = 0.2
    active_model: Optional[str] = None
    is_available: bool = False

class IntentPlan(BaseModel):
    task: Literal["vqa", "captioning", "grounding", "change_analysis", "optical_sar_fusion"]
    confidence: float = Field(default=0.90, ge=0.0, le=1.0)
    reasoning: str
    target_entity: Optional[str] = None
    target_features: List[str] = Field(default_factory=list)
    requires_multimodal: bool = False
    requires_temporal: bool = False

class PlanStep(BaseModel):
    step_id: int
    tool_name: str
    action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    objective: str

class ExecutionPlan(BaseModel):
    query: str
    complexity: Literal["simple", "medium", "complex"] = "simple"
    task: str
    selected_model_role: ModelRole = "planner"
    selected_model_tag: str
    steps: List[PlanStep] = Field(default_factory=list)
    reasoning: str

    @property
    def intent(self) -> IntentPlan:
        return IntentPlan(task=self.task, confidence=0.92, reasoning=self.reasoning)

class LLMGenerationResponse(BaseModel):
    text: str
    model: str
    role: ModelRole
    latency_ms: float
    success: bool = True
    error: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None

    @property
    def content(self) -> str:
        return self.text

    @property
    def model_name(self) -> str:
        return self.model

