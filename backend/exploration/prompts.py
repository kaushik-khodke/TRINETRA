"""
TRINETRA / Shanetra Geospatial Exploration Engine
AI Exploration Prompt Templates & System Guardrails
Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
Strict system prompts with explicit negative constraints forbidding hallucinated coordinates and code execution.
"""

from typing import Any, Dict, List, Optional
from exploration.ai_schemas import ExploreIntent


INTENT_CLASSIFIER_SYSTEM_PROMPT = """You are TRINETRA's Fast Intent Classifier for the Shanetra Earth Observation exploration workspace.
Your sole job is to classify the user's intent into exactly one of:
- 'navigation': moving the globe, centering on a location, flying to coordinates/places.
- 'layer_control': showing, hiding, removing, or adjusting opacity of map layers.
- 'dataset_search': finding, listing, or querying satellite observations/imagery for an area.
- 'view_control': zooming in, zooming out, switching view perspective.
- 'reset': returning the globe or camera to initial overview.
- 'combined': multi-part request combining navigation and layer control.
- 'unsupported': request requiring deep scientific Earth observation analysis (e.g. flood detection, change detection, NDVI calculation, vehicle counting, VQA, damage reports), or unrelated general conversation.

CRITICAL RULES:
1. Extract 'location_query' if a named place is mentioned.
2. Extract 'dataset_query' if a dataset or satellite type is mentioned (e.g., 'Sentinel-2', 'SAR', 'radar').
3. If the user asks for scientific analysis ('what changed', 'detect flooding', 'measure vegetation', 'find damage'), classify as 'unsupported' with a clear unsupported_reason explaining that analytical models belong to later phases.
4. Respond ONLY with the requested structured JSON schema."""


COMMAND_PLANNER_SYSTEM_PROMPT = """You are TRINETRA's Controlled Explore Command Planner for the Shanetra Earth workstation.
Translate the user's request and classified intent into a structured sequence of map commands.

STRICT CONSTRAINTS & SECURITY POLICIES:
1. You may ONLY output commands from the provided schema:
   - FLY_TO
   - ZOOM_IN
   - ZOOM_OUT
   - RESET_VIEW
   - SHOW_LAYER
   - HIDE_LAYER
   - SET_LAYER_OPACITY
   - REMOVE_LAYER
   - SET_AOI
   - CLEAR_AOI
   - SEARCH_DATASETS
   - ADD_DATASET_LAYER
2. NEVER output commands like CREATE_WORKSPACE, SHOW_TIMELINE, FIND_SIMILAR, RUN_ANALYSIS, or custom tool names. They do NOT exist in this exploration schema and will be rejected.
3. When the user asks about landmarks, capitals, geographical features, or places (e.g. 'capital of India', 'financial capital', 'Silicon Valley of India', 'Eiffel tower'), resolve it to the specific city or location name, put it in 'location_query' (e.g. 'New Delhi'), and emit a FLY_TO command.
4. NEVER invent or fabricate latitude/longitude coordinates! Instead, put the place name in 'location_query'. The backend's GeoResolver will resolve coordinates.
5. NEVER invent dataset IDs or observation hashes! Use 'SEARCH_DATASETS' with collection names (e.g. 'Sentinel-2').
6. You may ONLY reference layer IDs present in the ALLOWED LAYERS list. Do NOT invent new layer IDs.
7. You may NOT create URLs, file paths, or execute scripts.
8. Maximum commands in a plan is 6.
9. Return ONLY the structured JSON command plan."""


def build_intent_prompt(query: str, current_view: Optional[Dict[str, Any]] = None) -> str:
    """Builds a compact prompt for the fast intent router."""
    view_summary = ""
    if current_view:
        lat = current_view.get("latitude", 20.0)
        lon = current_view.get("longitude", 78.0)
        zoom = current_view.get("zoom", 5.0)
        view_summary = f"Current Viewport: Lat {lat:.2f}, Lon {lon:.2f}, Zoom {zoom:.1f}\n"

    return f"{view_summary}User Request: \"{query}\"\nClassify the exploration intent."


def build_planner_prompt(
    query: str,
    intent: ExploreIntent,
    available_layers: List[Dict[str, str]],
    active_layers: List[str],
    current_view: Optional[Dict[str, Any]] = None,
) -> str:
    """Builds a bounded prompt for the command planner model."""
    allowed_layers_text = "\n".join([f"- ID: {l['id']} | Name: {l['name']}" for l in available_layers])
    active_text = ", ".join(active_layers) if active_layers else "None (only base dark)"

    view_text = "Overview"
    if current_view:
        view_text = f"Lat {current_view.get('latitude', 20.0):.2f}, Lon {current_view.get('longitude', 78.0):.2f}, Zoom {current_view.get('zoom', 5.0):.1f}"

    return f"""User Request: "{query}"
Resolved Intent: {intent.intent.value}
Extracted Location: {intent.location_query or 'None'}
Extracted Dataset: {intent.dataset_query or 'None'}
Current Camera: {view_text}
Currently Active Layers: {active_text}

ALLOWED LAYERS:
{allowed_layers_text}

Generate the exact sequence of Explore commands needed."""
