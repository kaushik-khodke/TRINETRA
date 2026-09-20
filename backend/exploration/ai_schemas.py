"""
TRINETRA / Shanetra Geospatial Exploration Engine
Explore AI Schemas & Discriminated Command Definitions
Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
Strict, typed Pydantic models for intent classification, command planning, and execution contracts.
"""

from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator, ConfigDict


# Hard limit to prevent command flooding
MAX_AI_COMMANDS_PER_REQUEST = 6

# Error taxonomy codes
EXPLORE_QUERY_EMPTY = "EXPLORE_QUERY_EMPTY"
EXPLORE_QUERY_TOO_LONG = "EXPLORE_QUERY_TOO_LONG"
EXPLORE_INTENT_UNKNOWN = "EXPLORE_INTENT_UNKNOWN"
EXPLORE_LLM_TIMEOUT = "EXPLORE_LLM_TIMEOUT"
EXPLORE_LLM_INVALID_OUTPUT = "EXPLORE_LLM_INVALID_OUTPUT"
EXPLORE_LOCATION_AMBIGUOUS = "EXPLORE_LOCATION_AMBIGUOUS"
EXPLORE_LOCATION_NOT_FOUND = "EXPLORE_LOCATION_NOT_FOUND"
EXPLORE_COMMAND_REJECTED = "EXPLORE_COMMAND_REJECTED"
EXPLORE_LAYER_NOT_ALLOWED = "EXPLORE_LAYER_NOT_ALLOWED"
EXPLORE_DATASET_NOT_FOUND = "EXPLORE_DATASET_NOT_FOUND"
EXPLORE_PROVIDER_UNAVAILABLE = "EXPLORE_PROVIDER_UNAVAILABLE"
EXPLORE_COMMAND_FAILED = "EXPLORE_COMMAND_FAILED"


# --- 1. Intent Classification ---

class ExploreIntentType(str, Enum):
    NAVIGATION = "navigation"
    LAYER_CONTROL = "layer_control"
    DATASET_SEARCH = "dataset_search"
    VIEW_CONTROL = "view_control"
    RESET = "reset"
    COMBINED = "combined"
    UNSUPPORTED = "unsupported"


class ExploreIntent(BaseModel):
    """Structured intent representation produced by fast_router."""
    model_config = ConfigDict(extra="forbid")

    intent: ExploreIntentType = Field(..., description="High-level category of user intention")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    location_query: Optional[str] = Field(None, description="Extracted place name or coordinates (e.g. Nagpur)")
    dataset_query: Optional[str] = Field(None, description="Extracted dataset category (e.g. Sentinel-2)")
    requested_layers: List[str] = Field(default_factory=list, description="Explicit layer names or aliases mentioned")
    requested_actions: List[str] = Field(default_factory=list, description="Actions identified (e.g. show, fly_to)")
    unsupported_reason: Optional[str] = Field(None, description="Explanation if request requires deep scientific analysis")


# --- 2. Discriminated AI Command Models ---

class FlyToCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["FLY_TO"] = "FLY_TO"
    location_query: Optional[str] = Field(None, description="Named place to be resolved by GeoResolver")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    zoom: Optional[float] = Field(None, ge=0.0, le=24.0)
    heading: Optional[float] = Field(0.0, ge=0.0, le=360.0)
    pitch: Optional[float] = Field(0.0, ge=-90.0, le=90.0)
    duration: Optional[float] = Field(1.5, ge=0.1, le=10.0)


class ZoomInCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["ZOOM_IN"] = "ZOOM_IN"
    step: float = Field(1.0, ge=0.1, le=5.0)


class ZoomOutCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["ZOOM_OUT"] = "ZOOM_OUT"
    step: float = Field(1.0, ge=0.1, le=5.0)


class ResetViewCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["RESET_VIEW"] = "RESET_VIEW"


class ShowLayerCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["SHOW_LAYER"] = "SHOW_LAYER"
    layer_id: str = Field(..., min_length=1, max_length=128)


class HideLayerCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["HIDE_LAYER"] = "HIDE_LAYER"
    layer_id: str = Field(..., min_length=1, max_length=128)


class SetOpacityCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["SET_LAYER_OPACITY"] = "SET_LAYER_OPACITY"
    layer_id: str = Field(..., min_length=1, max_length=128)
    opacity: float = Field(..., ge=0.0, le=1.0)


class RemoveLayerCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["REMOVE_LAYER"] = "REMOVE_LAYER"
    layer_id: str = Field(..., min_length=1, max_length=128)


class SearchDatasetsCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["SEARCH_DATASETS"] = "SEARCH_DATASETS"
    query: Optional[str] = Field(None, max_length=200)
    location_query: Optional[str] = Field(None, max_length=100)
    collection: Optional[str] = Field(None, max_length=100)
    max_results: int = Field(10, ge=1, le=50)


class AddDatasetLayerCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["ADD_DATASET_LAYER"] = "ADD_DATASET_LAYER"
    asset_id: str = Field(..., min_length=1, max_length=128)
    title: Optional[str] = Field(None, max_length=128)


# --- Phase 4 AI Temporal & AOI Commands ---

class SetAOICommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["SET_AOI"] = "SET_AOI"
    geometry: Optional[Dict[str, Any]] = Field(None, description="GeoJSON Polygon geometry")
    bbox: Optional[List[float]] = Field(None, description="Bounding box [min_lon, min_lat, max_lon, max_lat]")


class ClearAOICommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["CLEAR_AOI"] = "CLEAR_AOI"


class SetDateRangeCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["SET_DATE_RANGE"] = "SET_DATE_RANGE"
    start_date: str = Field(..., description="Start ISO-8601 date")
    end_date: str = Field(..., description="End ISO-8601 date")


class SelectObservationCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["SELECT_OBSERVATION"] = "SELECT_OBSERVATION"
    observation_id: str = Field(..., min_length=1, max_length=128)
    target_slot: Literal["primary", "compare_a", "compare_b"] = "primary"


class CompareObservationsCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["COMPARE_OBSERVATIONS"] = "COMPARE_OBSERVATIONS"
    observation_a_id: str = Field(..., min_length=1, max_length=128)
    observation_b_id: str = Field(..., min_length=1, max_length=128)
    mode: Literal["split", "side_by_side", "opacity"] = "split"


ExploreCommand = Annotated[
    Union[
        FlyToCommand,
        ZoomInCommand,
        ZoomOutCommand,
        ResetViewCommand,
        ShowLayerCommand,
        HideLayerCommand,
        SetOpacityCommand,
        RemoveLayerCommand,
        SearchDatasetsCommand,
        AddDatasetLayerCommand,
        SetAOICommand,
        ClearAOICommand,
        SetDateRangeCommand,
        SelectObservationCommand,
        CompareObservationsCommand,
    ],
    Field(discriminator="type"),
]



# --- 3. Structured Command Plan ---

class ExploreCommandPlan(BaseModel):
    """Structured output emitted by the command planner model."""
    model_config = ConfigDict(extra="forbid")

    intent: str = Field(..., description="Summary intent code (e.g. navigation, combined)")
    summary: str = Field(..., description="Concise explanation of proposed map operations")
    commands: List[ExploreCommand] = Field(..., max_length=MAX_AI_COMMANDS_PER_REQUEST)

    @field_validator("commands")
    @classmethod
    def validate_command_limit(cls, v: List[ExploreCommand]) -> List[ExploreCommand]:
        if len(v) > MAX_AI_COMMANDS_PER_REQUEST:
            raise ValueError(f"Exceeded maximum commands per request ({MAX_AI_COMMANDS_PER_REQUEST})")
        return v


# --- 4. API Request & Execution Response Models ---

class ExploreViewStateContext(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    zoom: float = Field(..., ge=0.0, le=24.0)
    mode: Literal["2d", "3d"] = "2d"


class ExploreAIQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    view_state: Optional[ExploreViewStateContext] = None
    active_layer_ids: List[str] = Field(default_factory=list)
    explore_state_version: Optional[int] = 1


class CommandExecutionStatus(str, Enum):
    ACCEPTED = "accepted"
    EXECUTED = "executed"
    NO_OP = "no_op"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CommandExecutionItem(BaseModel):
    command_id: str
    type: str
    status: CommandExecutionStatus
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class ExploreStatePatch(BaseModel):
    camera: Optional[Dict[str, Any]] = None
    visible_layer_ids: Optional[List[str]] = None
    layer_opacities: Optional[Dict[str, float]] = None
    active_dataset_id: Optional[str] = None
    aoi: Optional[Dict[str, Any]] = None
    date_range: Optional[Dict[str, str]] = None
    selected_observation_id: Optional[str] = None
    comparison: Optional[Dict[str, Any]] = None



class ExploreAIQueryResponse(BaseModel):
    request_id: str
    status: Literal["completed", "partial_failure", "rejected", "error"]
    summary: str
    intent: str
    fast_path: bool = False
    commands: List[CommandExecutionItem]
    state_patch: ExploreStatePatch
    error_code: Optional[str] = None
    latency_ms: float = 0.0


class ExploreAIStatusResponse(BaseModel):
    available: bool
    model: str
    router_model: str
    planner_model: str
    structured_output: bool
    offline_fallback_active: bool
