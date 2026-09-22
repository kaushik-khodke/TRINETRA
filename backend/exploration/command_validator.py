"""
TRINETRA / Shanetra Geospatial Exploration Engine
AI Command Validator
Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
Strict multi-tier policy and security validation pipeline for AI-generated commands.
Prevents arbitrary execution, injection, unauthorized layer access, and coordinate anomalies.
"""

from typing import Dict, List, Optional, Tuple, Any
from exploration.ai_schemas import (
    ExploreCommand,
    ExploreCommandPlan,
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
    MAX_AI_COMMANDS_PER_REQUEST,
    EXPLORE_COMMAND_REJECTED,
    EXPLORE_LAYER_NOT_ALLOWED,
    EXPLORE_DATASET_NOT_FOUND,
)
from exploration.aoi.validator import AOIValidator
from exploration.comparison.validator import ComparisonValidator
from exploration.service import explore_service
from exploration.policies import LayerPolicyEngine


ALLOWED_COMMAND_TYPES = {
    "FLY_TO",
    "ZOOM_IN",
    "ZOOM_OUT",
    "RESET_VIEW",
    "SHOW_LAYER",
    "HIDE_LAYER",
    "SET_LAYER_OPACITY",
    "REMOVE_LAYER",
    "SEARCH_DATASETS",
    "ADD_DATASET_LAYER",
    "SET_AOI",
    "CLEAR_AOI",
    "SET_DATE_RANGE",
    "SELECT_OBSERVATION",
    "COMPARE_OBSERVATIONS",
    "RUN_ANALYSIS",
    "FOCUS_FINDING",
    "SHOW_EVIDENCE",
    "RUN_INVESTIGATION",
    "FOCUS_EVIDENCE",
    "SHOW_TIMELINE",
    "TRACK_OBJECT",
    "COMPARE_REGIONS",
    "SEARCH_INTELLIGENCE",
    "OPEN_EVENT",
    "OPEN_FINDING",
    "FIND_SIMILAR",
    "RUN_TEMPLATE",
    "CREATE_MONITOR",
    "SHOW_ANOMALIES",
    "SHOW_HOTSPOTS",
    "OPEN_WORKSPACE",
    "CREATE_WORKSPACE",
    "PIN_TO_BOARD",
    "RUN_INVESTIGATION_PLAN",
    "EXPORT_REPORT",
}




class CommandValidator:
    """Multi-stage validation engine enforcing strict security and policy boundaries."""

    @classmethod
    def validate_plan(
        cls,
        plan: ExploreCommandPlan,
        active_layer_ids: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validates the overall command plan.
        Returns (is_valid, error_code, error_message).
        """
        if not plan or not isinstance(plan.commands, list):
            return False, EXPLORE_COMMAND_REJECTED, "Malformed command plan."

        if len(plan.commands) == 0:
            return False, EXPLORE_COMMAND_REJECTED, "Plan contains 0 commands."

        if len(plan.commands) > MAX_AI_COMMANDS_PER_REQUEST:
            return (
                False,
                EXPLORE_COMMAND_REJECTED,
                f"Command count ({len(plan.commands)}) exceeds maximum limit of {MAX_AI_COMMANDS_PER_REQUEST}.",
            )

        active_ids = active_layer_ids or []

        for idx, cmd in enumerate(plan.commands):
            ok, err_code, err_msg = cls.validate_command(cmd, active_ids)
            if not ok:
                return False, err_code, f"Command #{idx + 1} ({getattr(cmd, 'type', 'UNKNOWN')}): {err_msg}"

        return True, None, None

    @classmethod
    def validate_command(
        cls,
        cmd: Any,
        active_layer_ids: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validates an individual command object.
        Returns (is_valid, error_code, error_message).
        """
        # 1. Type and structure check
        if isinstance(cmd, dict):
            cmd_type = cmd.get("type")
        else:
            cmd_type = getattr(cmd, "type", None)

        if not cmd_type or cmd_type not in ALLOWED_COMMAND_TYPES:
            return (
                False,
                EXPLORE_COMMAND_REJECTED,
                f"Command type '{cmd_type}' is unrecognized or prohibited.",
            )

        # 2. Specific command checks
        if cmd_type == "FLY_TO":
            return cls._validate_fly_to(cmd)

        elif cmd_type in ("ZOOM_IN", "ZOOM_OUT", "RESET_VIEW"):
            return True, None, None

        elif cmd_type in ("SHOW_LAYER", "HIDE_LAYER", "REMOVE_LAYER"):
            layer_id = getattr(cmd, "layer_id", None) if not isinstance(cmd, dict) else cmd.get("layer_id")
            return cls.validate_layer(layer_id, active_layer_ids)

        elif cmd_type == "SET_LAYER_OPACITY":
            layer_id = getattr(cmd, "layer_id", None) if not isinstance(cmd, dict) else cmd.get("layer_id")
            opacity = getattr(cmd, "opacity", None) if not isinstance(cmd, dict) else cmd.get("opacity")
            return cls._validate_set_opacity(layer_id, opacity, active_layer_ids)

        elif cmd_type == "SEARCH_DATASETS":
            return True, None, None

        elif cmd_type == "ADD_DATASET_LAYER":
            asset_id = getattr(cmd, "asset_id", None) if not isinstance(cmd, dict) else cmd.get("asset_id")
            return cls.validate_dataset(asset_id)

        elif cmd_type == "SET_AOI":
            geom = getattr(cmd, "geometry", None) if not isinstance(cmd, dict) else cmd.get("geometry")
            bbox = getattr(cmd, "bbox", None) if not isinstance(cmd, dict) else cmd.get("bbox")
            if not geom and not bbox:
                return False, EXPLORE_COMMAND_REJECTED, "SET_AOI requires geometry or bbox."
            if geom:
                val = AOIValidator.validate(geom)
                if not val.valid:
                    return False, EXPLORE_COMMAND_REJECTED, f"Invalid AOI geometry: {'; '.join(val.errors)}"
            if bbox:
                if len(bbox) != 4 or bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
                    return False, EXPLORE_COMMAND_REJECTED, "Invalid bounding box format."
            return True, None, None

        elif cmd_type == "CLEAR_AOI":
            return True, None, None

        elif cmd_type == "SET_DATE_RANGE":
            start_date = getattr(cmd, "start_date", None) if not isinstance(cmd, dict) else cmd.get("start_date")
            end_date = getattr(cmd, "end_date", None) if not isinstance(cmd, dict) else cmd.get("end_date")
            if not start_date or not end_date:
                return False, EXPLORE_COMMAND_REJECTED, "SET_DATE_RANGE requires start_date and end_date."
            if str(start_date) > str(end_date):
                return False, EXPLORE_COMMAND_REJECTED, f"start_date ({start_date}) cannot be after end_date ({end_date})."
            return True, None, None

        elif cmd_type == "SELECT_OBSERVATION":
            obs_id = getattr(cmd, "observation_id", None) if not isinstance(cmd, dict) else cmd.get("observation_id")
            if not obs_id or not isinstance(obs_id, str):
                return False, EXPLORE_COMMAND_REJECTED, "SELECT_OBSERVATION requires a valid observation_id."
            obs = explore_service.get_observation(obs_id)
            if not obs:
                return False, EXPLORE_COMMAND_REJECTED, f"Observation '{obs_id}' not found."
            return True, None, None

        elif cmd_type == "COMPARE_OBSERVATIONS":
            obs_a_id = getattr(cmd, "observation_a_id", None) if not isinstance(cmd, dict) else cmd.get("observation_a_id")
            obs_b_id = getattr(cmd, "observation_b_id", None) if not isinstance(cmd, dict) else cmd.get("observation_b_id")
            if not obs_a_id or not obs_b_id:
                return False, EXPLORE_COMMAND_REJECTED, "COMPARE_OBSERVATIONS requires observation_a_id and observation_b_id."
            if obs_a_id == obs_b_id:
                return False, EXPLORE_COMMAND_REJECTED, "Cannot compare an observation with itself."
            obs_a = explore_service.get_observation(obs_a_id)
            obs_b = explore_service.get_observation(obs_b_id)
            if not obs_a:
                return False, EXPLORE_COMMAND_REJECTED, f"Observation A '{obs_a_id}' not found."
            if not obs_b:
                return False, EXPLORE_COMMAND_REJECTED, f"Observation B '{obs_b_id}' not found."
            res = ComparisonValidator.validate(obs_a, obs_b)
            if not res.compatible:
                return False, EXPLORE_COMMAND_REJECTED, f"Observations incompatible: {'; '.join(res.errors)}"
            return True, None, None

        elif cmd_type == "RUN_ANALYSIS":
            mode = getattr(cmd, "mode", None) if not isinstance(cmd, dict) else cmd.get("mode")
            if mode and mode not in ("BI_TEMPORAL", "SAR_OPTICAL", "SINGLE_IMAGE"):
                return False, EXPLORE_COMMAND_REJECTED, f"Invalid analysis mode '{mode}'."
            return True, None, None

        elif cmd_type == "FOCUS_FINDING":
            finding_id = getattr(cmd, "finding_id", None) if not isinstance(cmd, dict) else cmd.get("finding_id")
            if not finding_id or not isinstance(finding_id, str):
                return False, EXPLORE_COMMAND_REJECTED, "FOCUS_FINDING requires a valid finding_id."
            lat = getattr(cmd, "latitude", None) if not isinstance(cmd, dict) else cmd.get("latitude")
            lon = getattr(cmd, "longitude", None) if not isinstance(cmd, dict) else cmd.get("longitude")
            if lat is not None and (lat < -90.0 or lat > 90.0):
                return False, EXPLORE_COMMAND_REJECTED, f"Latitude {lat} out of bounds."
            if lon is not None and (lon < -180.0 or lon > 180.0):
                return False, EXPLORE_COMMAND_REJECTED, f"Longitude {lon} out of bounds."
            return True, None, None

        elif cmd_type == "SHOW_EVIDENCE":
            evidence_id = getattr(cmd, "evidence_id", None) if not isinstance(cmd, dict) else cmd.get("evidence_id")
            if not evidence_id or not isinstance(evidence_id, str):
                return False, EXPLORE_COMMAND_REJECTED, "SHOW_EVIDENCE requires a valid evidence_id."
            return True, None, None

        elif cmd_type == "RUN_INVESTIGATION":
            q = getattr(cmd, "question", None) if not isinstance(cmd, dict) else cmd.get("question")
            if not q or len(str(q).strip()) < 3:
                return False, EXPLORE_COMMAND_REJECTED, "RUN_INVESTIGATION requires question with at least 3 characters."
            return True, None, None

        elif cmd_type == "FOCUS_EVIDENCE":
            ev_id = getattr(cmd, "evidence_id", None) if not isinstance(cmd, dict) else cmd.get("evidence_id")
            if not ev_id:
                return False, EXPLORE_COMMAND_REJECTED, "FOCUS_EVIDENCE requires evidence_id."
            return True, None, None

        elif cmd_type in ("SHOW_TIMELINE", "TRACK_OBJECT", "COMPARE_REGIONS"):
            return True, None, None

        # Phase 7 Commands
        elif cmd_type == "SEARCH_INTELLIGENCE":
            q = getattr(cmd, "query", None) if not isinstance(cmd, dict) else cmd.get("query")
            if not q or len(str(q).strip()) == 0:
                return False, EXPLORE_COMMAND_REJECTED, "SEARCH_INTELLIGENCE requires a non-empty query string."
            return True, None, None

        elif cmd_type == "OPEN_EVENT":
            ev_id = getattr(cmd, "event_id", None) if not isinstance(cmd, dict) else cmd.get("event_id")
            if not ev_id:
                return False, EXPLORE_COMMAND_REJECTED, "OPEN_EVENT requires event_id."
            return True, None, None

        elif cmd_type == "OPEN_FINDING":
            f_id = getattr(cmd, "finding_id", None) if not isinstance(cmd, dict) else cmd.get("finding_id")
            if not f_id:
                return False, EXPLORE_COMMAND_REJECTED, "OPEN_FINDING requires finding_id."
            return True, None, None

        elif cmd_type == "FIND_SIMILAR":
            e_id = getattr(cmd, "event_id", None) if not isinstance(cmd, dict) else cmd.get("event_id")
            f_id = getattr(cmd, "finding_id", None) if not isinstance(cmd, dict) else cmd.get("finding_id")
            if not e_id and not f_id:
                return False, EXPLORE_COMMAND_REJECTED, "FIND_SIMILAR requires either event_id or finding_id."
            return True, None, None

        elif cmd_type == "RUN_TEMPLATE":
            t_id = getattr(cmd, "template_id", None) if not isinstance(cmd, dict) else cmd.get("template_id")
            if not t_id:
                return False, EXPLORE_COMMAND_REJECTED, "RUN_TEMPLATE requires template_id."
            return True, None, None

        elif cmd_type == "CREATE_MONITOR":
            m_name = getattr(cmd, "name", None) if not isinstance(cmd, dict) else cmd.get("name")
            if not m_name or len(str(m_name).strip()) == 0:
                return False, EXPLORE_COMMAND_REJECTED, "CREATE_MONITOR requires a monitor name."
            return True, None, None

        elif cmd_type == "SHOW_ANOMALIES":
            score = getattr(cmd, "min_score", None) if not isinstance(cmd, dict) else cmd.get("min_score")
            if score is not None and (score < 0.0 or score > 1.0):
                return False, EXPLORE_COMMAND_REJECTED, "SHOW_ANOMALIES min_score must be between 0.0 and 1.0."
            return True, None, None

        elif cmd_type == "SHOW_HOTSPOTS":
            return True, None, None

        return False, EXPLORE_COMMAND_REJECTED, f"Unsupported command '{cmd_type}'."



    @classmethod
    def validate_layer(
        cls,
        layer_id: Optional[str],
        active_layer_ids: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Enforces layer existence, active policy, and AI control permissions.
        """
        if not layer_id or not isinstance(layer_id, str):
            return False, EXPLORE_LAYER_NOT_ALLOWED, "Invalid or missing layer ID."

        # Query authoritative exploration service layer registry
        layer = explore_service.get_layer(layer_id)
        if not layer:
            return False, EXPLORE_LAYER_NOT_ALLOWED, f"Layer '{layer_id}' does not exist in registry."

        if not layer.enabled:
            return False, EXPLORE_LAYER_NOT_ALLOWED, f"Layer '{layer_id}' is administratively disabled."

        if not layer.ai_controllable:
            return (
                False,
                EXPLORE_LAYER_NOT_ALLOWED,
                f"Layer '{layer_id}' is restricted from AI automated control (ai_controllable=False).",
            )

        return True, None, None

    @classmethod
    def validate_dataset(cls, asset_id: Optional[str]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validates asset ID security format and existence in catalog.
        """
        if not asset_id or not isinstance(asset_id, str):
            return False, EXPLORE_DATASET_NOT_FOUND, "Missing or invalid asset ID."

        if not LayerPolicyEngine.validate_safe_asset_id(asset_id):
            return False, EXPLORE_COMMAND_REJECTED, "Asset ID violates security policy (path traversal rejected)."

        asset = explore_service.get_asset(asset_id)
        if not asset:
            return False, EXPLORE_DATASET_NOT_FOUND, f"Asset '{asset_id}' not found in local or remote index."

        return True, None, None

    @classmethod
    def _validate_fly_to(cls, cmd: Any) -> Tuple[bool, Optional[str], Optional[str]]:
        lat = getattr(cmd, "latitude", None) if not isinstance(cmd, dict) else cmd.get("latitude")
        lon = getattr(cmd, "longitude", None) if not isinstance(cmd, dict) else cmd.get("longitude")
        zoom = getattr(cmd, "zoom", None) if not isinstance(cmd, dict) else cmd.get("zoom")
        loc_query = getattr(cmd, "location_query", None) if not isinstance(cmd, dict) else cmd.get("location_query")

        # Either coordinates or location_query must be present
        if lat is None and lon is None and not loc_query:
            return False, EXPLORE_COMMAND_REJECTED, "FLY_TO requires either coordinates or location_query."

        if lat is not None:
            if not isinstance(lat, (int, float)) or lat < -90.0 or lat > 90.0:
                return False, EXPLORE_COMMAND_REJECTED, f"Latitude {lat} out of valid bounds [-90, 90]."

        if lon is not None:
            if not isinstance(lon, (int, float)) or lon < -180.0 or lon > 180.0:
                return False, EXPLORE_COMMAND_REJECTED, f"Longitude {lon} out of valid bounds [-180, 180]."

        if zoom is not None:
            if not isinstance(zoom, (int, float)) or zoom < 0.0 or zoom > 24.0:
                return False, EXPLORE_COMMAND_REJECTED, f"Zoom {zoom} out of valid bounds [0, 24]."

        return True, None, None

    @classmethod
    def _validate_set_opacity(
        cls,
        layer_id: Optional[str],
        opacity: Optional[float],
        active_layer_ids: Optional[List[str]],
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        ok, err_code, err_msg = cls.validate_layer(layer_id, active_layer_ids)
        if not ok:
            return False, err_code, err_msg

        if opacity is None or not isinstance(opacity, (int, float)):
            return False, EXPLORE_COMMAND_REJECTED, "Opacity must be a valid floating-point number."

        if opacity < 0.0 or opacity > 1.0:
            return False, EXPLORE_COMMAND_REJECTED, f"Opacity {opacity} is out of bounds [0.0, 1.0]."

        return True, None, None
