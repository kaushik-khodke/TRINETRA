"""
TRINETRA Analysis Engine — Request Planner
Determines analysis mode, required observations, assets, and preprocessing pipeline.
Favors deterministic routing for explicit requests, falling back to NLP intent classification only for ambiguous queries.
"""

import re
from typing import Dict, Any, Optional, Tuple, List
from analysis_engine.schemas import AnalysisMode, AnalysisRequest
from analysis_engine.errors import InputFailureError


class AnalysisPlanner:
    """Plans the analytical pipeline from structured or natural language input."""

    @classmethod
    def plan(
        cls,
        request: AnalysisRequest,
        resolved_observations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Derives mode, selected observation assignments, and target task.
        """
        mode = request.mode
        clean_query = request.query.strip().lower()

        # 1. Deterministic mode resolution if explicit or obvious from observations
        if not mode:
            mode = cls._infer_mode(clean_query, resolved_observations)

        # 2. Assign and validate required observations
        obs_a, obs_b = cls._assign_observations(mode, resolved_observations, request)

        # 3. Determine specific task within the mode
        task = cls._infer_task(mode, clean_query)

        return {
            "mode": mode,
            "task": task,
            "observation_a": obs_a,
            "observation_b": obs_b,
            "query": request.query,
            "options": request.options,
        }

    @classmethod
    def _infer_mode(
        cls,
        query: str,
        observations: List[Dict[str, Any]],
    ) -> AnalysisMode:
        """Determines analytical mode based on keyword heuristics and observation count/modalities."""
        # Check explicit SAR keywords
        if any(w in query for w in ["sar", "radar", "flood", "inundation", "microwave", "cross-modal", "multimodal"]):
            # If two observations and one is SAR, this is SAR-Optical
            modalities = [o.get("modality", "").lower() for o in observations]
            if len(observations) >= 2 and ("sar" in modalities or any("s1" in o.get("id", "").lower() for o in observations)):
                return AnalysisMode.SAR_OPTICAL
            if len(observations) >= 2:
                return AnalysisMode.SAR_OPTICAL

        # Check explicit change keywords
        if any(w in query for w in ["change", "compare", "difference", "between", "shift", "expansion", "growth", "lost", "decrease", "increase", "temporal"]):
            if len(observations) >= 2:
                return AnalysisMode.BI_TEMPORAL

        # Check observation count heuristics
        if len(observations) >= 2:
            modalities = [o.get("modality", "").lower() for o in observations]
            if "sar" in modalities and "optical" in modalities:
                return AnalysisMode.SAR_OPTICAL
            return AnalysisMode.BI_TEMPORAL
        elif len(observations) == 1:
            return AnalysisMode.SINGLE_IMAGE

        # Default heuristic based on query
        if any(w in query for w in ["where", "find", "locate", "building", "road", "what is", "describe", "count"]):
            return AnalysisMode.SINGLE_IMAGE

        return AnalysisMode.BI_TEMPORAL

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
            a = obs_map.get(request.observation_a_id) if (request.observation_a_id and request.observation_a_id in obs_map) else ({"id": request.observation_a_id, "modality": "optical", "name": "Observation A (Baseline)"} if request.observation_a_id else (observations[0] if observations else {"id": "sentinel2_baseline_t1", "modality": "optical", "name": "Sentinel-2 Baseline (T1)"}))
            b = obs_map.get(request.observation_b_id) if (request.observation_b_id and request.observation_b_id in obs_map) else ({"id": request.observation_b_id, "modality": "optical", "name": "Observation B (Comparison)"} if request.observation_b_id else (observations[1] if len(observations) > 1 else {"id": "sentinel2_comparison_t2", "modality": "optical", "name": "Sentinel-2 Follow-up (T2)"}))
            if a.get("id") == b.get("id"):
                b = dict(b)
                b["id"] = f"{b.get('id')}_followup"
                b["name"] = f"{b.get('name', 'Observation')} (Follow-up)"
            return a, b

        elif mode == AnalysisMode.SAR_OPTICAL:
            cand_a = obs_map.get(request.observation_a_id) if (request.observation_a_id and request.observation_a_id in obs_map) else ({"id": request.observation_a_id, "modality": "optical", "name": "Optical Surface"} if request.observation_a_id else (observations[0] if observations else {"id": "sentinel2_optical_a", "modality": "optical", "name": "Sentinel-2 MSI Optical"}))
            cand_b = obs_map.get(request.observation_b_id) if (request.observation_b_id and request.observation_b_id in obs_map) else ({"id": request.observation_b_id, "modality": "sar", "name": "SAR Radar"} if request.observation_b_id else (observations[1] if len(observations) > 1 else {"id": "sentinel1_sar_b", "modality": "sar", "name": "Sentinel-1 C-SAR Radar"}))
            
            # Place optical in A, SAR in B
            if cand_a.get("modality", "").lower() == "sar" or "s1" in str(cand_a.get("id", "")).lower():
                return cand_b, cand_a
            return cand_a, cand_b

        else:  # SINGLE_IMAGE
            a = obs_map.get(request.observation_a_id) if (request.observation_a_id and request.observation_a_id in obs_map) else ({"id": request.observation_a_id, "modality": "optical", "name": "Scene Observation"} if request.observation_a_id else (observations[0] if observations else {"id": "target_observation", "modality": "optical", "name": "Current Satellite View"}))
            return a, None


    @classmethod
    def _infer_task(cls, mode: AnalysisMode, clean_query: str) -> str:
        """Determines the specific analytical subtask."""
        if mode == AnalysisMode.BI_TEMPORAL:
            return "change_detection"
        elif mode == AnalysisMode.SAR_OPTICAL:
            if any(w in clean_query for w in ["flood", "water", "inundation"]):
                return "inundation_detection"
            return "cross_modal_fusion"
        else:  # SINGLE_IMAGE
            if any(w in clean_query for w in ["where", "locate", "box", "find", "highlight", "detect"]):
                return "grounding"
            elif any(w in clean_query for w in ["describe", "caption", "scene", "overview"]):
                return "captioning"
            return "vqa"
