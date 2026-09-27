"""
TRINETRA / Shanetra Geospatial Exploration Engine
Explore AI Subgraph & State Machine
Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
Lightweight state machine executing query validation, intent classification,
context resolution, planning, validation, and command execution.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from exploration.ai_schemas import (
    ExploreAIQueryRequest,
    ExploreAIQueryResponse,
    ExploreIntent,
    ExploreCommandPlan,
    CommandExecutionItem,
    ExploreStatePatch,
)
from exploration.ai_service import explore_ai_service


class ExploreAIState(BaseModel):
    """Raw data state container for the Explore AI pipeline."""
    request_id: str
    query: str
    active_layer_ids: List[str] = Field(default_factory=list)
    view_state: Optional[Dict[str, Any]] = None
    intent: Optional[ExploreIntent] = None
    plan: Optional[ExploreCommandPlan] = None
    execution_items: List[CommandExecutionItem] = Field(default_factory=list)
    state_patch: Optional[ExploreStatePatch] = None
    status: str = "pending"
    summary: str = ""
    error_code: Optional[str] = None


class ExploreAIGraph:
    """Explicit workflow coordinator wrapping explore_ai_service."""

    @classmethod
    def run(cls, request: ExploreAIQueryRequest) -> ExploreAIQueryResponse:
        """Executes the complete Explore AI workflow."""
        return explore_ai_service.process_query(request)
