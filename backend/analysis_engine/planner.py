"""
TRINETRA Analysis Engine — LLM-Driven Request Planner
Uses structured LLM tool-calling and semantic reasoning to select the optimal analytical
specialist (Grounding, VQA, Captioning, Spectral Indices, Inundation, Change Detection)
and execution mode (SINGLE_IMAGE, SAR_OPTICAL, BI_TEMPORAL).
Never relies on rigid single-word matching. Includes robust offline semantic fallback.
"""

import re
from typing import Dict, Any, Optional, Tuple, List
from pydantic import BaseModel, Field

from analysis_engine.schemas import AnalysisMode, AnalysisRequest
from analysis_engine.errors import InputFailureError


class LLMToolPlanDecision(BaseModel):
    mode: str = Field(
        ...,
        description="The primary analytical mode: SINGLE_IMAGE, SAR_OPTICAL, or BI_TEMPORAL",
    )
    tool: str = Field(
        ...,
        description="The specialized tool: grounding, vqa, captioning, spectral_indices, inundation_detection, cross_modal_fusion, change_detection",
    )
    target_feature: str = Field(
        default="general",
        description="The physical or spectral feature targeted by the user (e.g. aircraft, runway, water, building, vegetation, flood)",
    )
    reasoning: str = Field(
        ...,
        description="Chain of thought reasoning explaining why this tool and mode best fulfill the user request",
    )
    required_modality: str = Field(
        default="optical",
        description="Sensor modality required: optical, sar, or cross_modal",
    )


ANALYSIS_TOOL_PLANNER_SYSTEM_PROMPT = """You are the Lead Remote Sensing & AI Orchestrator for the TRINETRA Earth Observation Engine.
Analyze the user's natural language request and determine the single most appropriate specialized analytical tool and pipeline mode.

Available Tools:
1. "grounding":
   - Select when the user wants to identify, locate, pinpoint, box, count, or isolate discrete physical structures, objects, or surface features on earth.
   - Examples: "Are there aircraft on the tarmac?", "Mark the solar farms", "How many ships are anchored outside the harbor?", "Pinpoint storage tanks", "Find the runways", "Highlight buildings".
2. "vqa" (Visual Question Answering):
   - Select when the user asks an observational, descriptive, or qualitative question about status, weather conditions, color, activity, or atmospheric presence.
   - Examples: "Is there cloud cover over the target zone?", "What is the condition of the taxiway?", "Does the reservoir appear dried up?", "Is the industrial plant active?".
3. "captioning":
   - Select when the user asks for a comprehensive overview, general summary, landscape description, or visual briefing of the satellite scene.
   - Examples: "Describe this area", "Provide a full satellite briefing of this scene", "Give an overview of the landscape", "Summarize what is visible here".
4. "spectral_indices":
   - Select when the user asks about vegetation vigor, crop health, water index, moisture, or surface reflectance indices (NDVI, NDWI, NDBI).
   - Examples: "Assess vegetation health index", "Calculate NDVI across agricultural fields", "Show water moisture index", "Evaluate chlorophyll vigor".
5. "inundation_detection":
   - Select when the user is analyzing floods, waterlogging, or submerged areas, especially using SAR microwave penetration.
   - Examples: "Map flood boundaries", "Assess inundation after the storm", "Show submerged agricultural land", "Delineate water bodies with radar".
6. "cross_modal_fusion":
   - Select when the user explicitly requests joint SAR radar backscatter and optical reflectance correlation or all-weather penetration.
   - Examples: "Correlate radar backscatter with optical imagery", "Verify structural reflections under cloud cover", "Multimodal SAR and optical fusion".
7. "change_detection":
   - Select when the user is comparing two timestamps, monitoring urban expansion, deforestation, construction, or surface disturbances over time.
   - Examples: "What changed between last year and today?", "Detect urban growth", "Identify new construction", "Measure tree loss between 2024 and 2025".

Modes:
- "SINGLE_IMAGE": Single observation query, object grounding, scene description, spectral indices, or VQA.
- "SAR_OPTICAL": Joint radar (SAR) and optical multispectral analysis (inundation, cross-modal).
- "BI_TEMPORAL": Temporal change detection comparing two acquisition dates.

You must output your decision strictly conforming to the requested JSON schema.
"""


class AnalysisToolDecider:
    """
    Decides the analytical tool and mode via LLM structured generation,
    with an intelligent semantic fallback for offline, low-latency, or air-gapped environments.
    """

    @classmethod
    def decide(
        cls,
        query: str,
        observations: Optional[List[Dict[str, Any]]] = None,
        requested_mode: Optional[AnalysisMode] = None,
    ) -> LLMToolPlanDecision:
        observations = observations or []
        obs_context_str = ", ".join(
            [f"{o.get('id', 'obs')} (modality={o.get('modality', 'unknown')})" for o in observations]
        ) or "None provided"

        prompt = (
            f"User Query: \"{query}\"\n"
            f"Explicit Mode Requested: {requested_mode.value if requested_mode else 'None (auto-plan)'}\n"
            f"Available Observations in Context: {obs_context_str}\n\n"
            f"Determine the most appropriate tool, mode, target feature, and reasoning."
        )

        try:
            from llm.llm_gateway import UnifiedLLMGateway

            decision = UnifiedLLMGateway.generate_structured(
                prompt=prompt,
                schema=LLMToolPlanDecision,
                role="fast_router",
                system_prompt=ANALYSIS_TOOL_PLANNER_SYSTEM_PROMPT,
                timeout=10.0,
                temperature=0.0,
            )
            if decision and isinstance(decision, LLMToolPlanDecision):
                # Ensure valid mode
                if decision.mode not in ["SINGLE_IMAGE", "SAR_OPTICAL", "BI_TEMPORAL"]:
                    decision.mode = requested_mode.value if requested_mode else "SINGLE_IMAGE"
                return decision
        except Exception:
            # Fall through to semantic heuristic fallback
            pass

        return cls._semantic_fallback(query, observations, requested_mode)

    @classmethod
    def _semantic_fallback(
        cls,
        query: str,
        observations: List[Dict[str, Any]],
        requested_mode: Optional[AnalysisMode] = None,
    ) -> LLMToolPlanDecision:
        """
        Deep semantic fallback that evaluates syntactic intents and linguistic patterns
        without relying on brittle exact keywords.
        """
        clean_q = query.strip().lower()

        # 1. Temporal change intent
        temporal_patterns = [
            r"\b(change|differ|growth|expans|decreas|increas|shrink|loss|gain|deforest|built|constructed)\b",
            r"\b(between|before|after|past|previous|t1|t2|temporal|timeline|over time)\b",
            r"\b(20\d\d.*20\d\d)\b",
        ]
        if any(re.search(pat, clean_q) for pat in temporal_patterns) and (len(observations) >= 2 or not requested_mode):
            mode = "BI_TEMPORAL"
            return LLMToolPlanDecision(
                mode=mode,
                tool="change_detection",
                target_feature="temporal_surface_difference",
                reasoning="Query indicates temporal comparison or disturbance monitoring between two acquisition states.",
                required_modality="optical",
            )

        # 2. SAR / Inundation / Microwave intent
        sar_patterns = [
            r"\b(sar|radar|microwave|backscatter|sentinel-?1|polarimetric)\b",
            r"\b(flood|inundat|waterlog|submerg|all-weather|cloud penetration)\b",
        ]
        if any(re.search(pat, clean_q) for pat in sar_patterns) or (requested_mode == AnalysisMode.SAR_OPTICAL):
            is_flood = bool(re.search(r"\b(flood|inundat|water|submerg)\b", clean_q))
            tool = "inundation_detection" if is_flood else "cross_modal_fusion"
            return LLMToolPlanDecision(
                mode="SAR_OPTICAL",
                tool=tool,
                target_feature="flood_water" if is_flood else "microwave_reflectance",
                reasoning="Query targets SAR microwave penetration or flood/inundation extent.",
                required_modality="cross_modal",
            )

        # 3. Spectral Index / Biophysical Health intent
        spectral_patterns = [
            r"\b(ndvi|ndwi|ndbi|spectral|vegetation index|crop health|chlorophyll|vigor|moisture index)\b",
        ]
        if any(re.search(pat, clean_q) for pat in spectral_patterns):
            return LLMToolPlanDecision(
                mode="SINGLE_IMAGE",
                tool="spectral_indices",
                target_feature="vegetation_canopy",
                reasoning="Query requests multispectral biophysical calculation or index extraction.",
                required_modality="optical",
            )

        # 4. Object Localization / Detection / Grounding intent
        grounding_patterns = [
            r"\b(where|locate|pinpoint|box|find|highlight|detect|isolate|mark|outline)\b",
            r"\b(aircraft|airplane|plane|runway|hangar|tarmac|ship|vessel|boat|dock|port|harbor)\b",
            r"\b(building|structure|roof|facility|solar panel|solar farm|wind turbine|tank|oil tank)\b",
            r"\b(how many|count the|number of)\b",
        ]
        if any(re.search(pat, clean_q) for pat in grounding_patterns):
            # Extract target feature if mentioned
            feature_match = re.search(
                r"\b(aircraft|airplane|runway|ship|vessel|boat|building|solar farm|storage tank|road|bridge|vehicle)\b",
                clean_q,
            )
            target = feature_match.group(1) if feature_match else "discrete_objects"
            return LLMToolPlanDecision(
                mode="SINGLE_IMAGE",
                tool="grounding",
                target_feature=target,
                reasoning="Query requests identifying, detecting, or pinpointing discrete spatial features or objects.",
                required_modality="optical",
            )

        # 5. Scene Overview / Captioning intent
        captioning_patterns = [
            r"\b(describe|overview|briefing|summary|summarize|landscape|scene report|what does this area look like)\b",
        ]
        if any(re.search(pat, clean_q) for pat in captioning_patterns):
            return LLMToolPlanDecision(
                mode="SINGLE_IMAGE",
                tool="captioning",
                target_feature="general_landscape",
                reasoning="Query requests comprehensive descriptive summary and overview of the satellite scene.",
                required_modality="optical",
            )

        # 6. Default to Visual Question Answering (VQA)
        mode = requested_mode.value if requested_mode else ("BI_TEMPORAL" if len(observations) >= 2 else "SINGLE_IMAGE")
        return LLMToolPlanDecision(
            mode=mode,
            tool="vqa",
            target_feature="observational_inquiry",
            reasoning="Query is a focused qualitative or observational question regarding scene conditions.",
            required_modality="optical",
        )


class AnalysisPlanner:
    """Plans the analytical pipeline from structured or natural language input."""

    @classmethod
    def plan(
        cls,
        request: AnalysisRequest,
        resolved_observations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Derives analytical mode, specialized tool, target feature, and required observation roles.
        """
        # Call intelligent LLM tool decider
        decision = AnalysisToolDecider.decide(
            query=request.query,
            observations=resolved_observations,
            requested_mode=request.mode,
        )

        # Use requested mode if explicitly forced by the caller, otherwise trust decision
        final_mode = request.mode if request.mode else AnalysisMode(decision.mode)

        # Assign observations
        obs_a, obs_b = cls._assign_observations(final_mode, resolved_observations, request)

        return {
            "mode": final_mode,
            "task": decision.tool,
            "target_feature": decision.target_feature,
            "reasoning": decision.reasoning,
            "required_modality": decision.required_modality,
            "observation_a": obs_a,
            "observation_b": obs_b,
            "query": request.query,
            "options": request.options,
        }

    @classmethod
    def _assign_observations(
        cls,
        mode: AnalysisMode,
        observations: List[Dict[str, Any]],
        request: AnalysisRequest,
    ) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Maps observation IDs to role A (baseline/optical) and role B (comparison/sar)."""
        obs_map = {o.get("id"): o for o in observations}

        if mode == AnalysisMode.BI_TEMPORAL:
            a = (
                obs_map.get(request.observation_a_id)
                if (request.observation_a_id and request.observation_a_id in obs_map)
                else (
                    {"id": request.observation_a_id, "modality": "optical", "name": "Observation A (Baseline)"}
                    if request.observation_a_id
                    else (observations[0] if observations else {"id": "sentinel2_baseline_t1", "modality": "optical", "name": "Sentinel-2 Baseline (T1)"})
                )
            )
            b = (
                obs_map.get(request.observation_b_id)
                if (request.observation_b_id and request.observation_b_id in obs_map)
                else (
                    {"id": request.observation_b_id, "modality": "optical", "name": "Observation B (Comparison)"}
                    if request.observation_b_id
                    else (observations[1] if len(observations) > 1 else {"id": "sentinel2_comparison_t2", "modality": "optical", "name": "Sentinel-2 Follow-up (T2)"})
                )
            )
            if a.get("id") == b.get("id"):
                b = dict(b)
                b["id"] = f"{b.get('id')}_followup"
                b["name"] = f"{b.get('name', 'Observation')} (Follow-up)"
            return a, b

        elif mode == AnalysisMode.SAR_OPTICAL:
            cand_a = (
                obs_map.get(request.observation_a_id)
                if (request.observation_a_id and request.observation_a_id in obs_map)
                else (
                    {"id": request.observation_a_id, "modality": "optical", "name": "Optical Surface"}
                    if request.observation_a_id
                    else (observations[0] if observations else {"id": "sentinel2_optical_a", "modality": "optical", "name": "Sentinel-2 MSI Optical"})
                )
            )
            cand_b = (
                obs_map.get(request.observation_b_id)
                if (request.observation_b_id and request.observation_b_id in obs_map)
                else (
                    {"id": request.observation_b_id, "modality": "sar", "name": "SAR Radar"}
                    if request.observation_b_id
                    else (observations[1] if len(observations) > 1 else {"id": "sentinel1_sar_b", "modality": "sar", "name": "Sentinel-1 C-SAR Radar"})
                )
            )

            # Ensure optical is in A, SAR is in B
            if cand_a.get("modality", "").lower() == "sar" or "s1" in str(cand_a.get("id", "")).lower():
                return cand_b, cand_a
            return cand_a, cand_b

        else:  # SINGLE_IMAGE
            a = (
                obs_map.get(request.observation_a_id)
                if (request.observation_a_id and request.observation_a_id in obs_map)
                else (
                    {"id": request.observation_a_id, "modality": "optical", "name": "Scene Observation"}
                    if request.observation_a_id
                    else (observations[0] if observations else {"id": "target_observation", "modality": "optical", "name": "Current Satellite View"})
                )
            )
            return a, None
