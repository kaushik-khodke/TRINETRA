"""
TRINETRA Workstation — Copilot Plan Generator
Translates natural-language researcher enquiries into typed, inspectable AnalysisPlan JSON
conforming to copilot-prompt-and-validation.md using UnifiedLLMGateway.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from .schemas import (
    AnalysisPlan,
    AnalysisPlanPipelineRef,
    AnalysisPlanInputBinding,
    PlanStatus,
)
from .pipeline_registry import PIPELINE_REGISTRY, list_pipelines
from .domain_validator import PlanDomainValidator

logger = logging.getLogger("trinetra.workstation.planner")


SYSTEM_PROMPT = """You are the planning component of the TRINETRA Satellite Research Workspace.
Your ONLY job is to create a typed, reviewable AnalysisPlan JSON object from the researcher's query.
You do NOT execute analysis. You do NOT invent assets, sensor IDs, dates, or measurements.

Available Pipelines:
- optical_change: For vegetation change, deforestation, urban growth, water boundary shifts using Sentinel-2 optical indices (NDVI/NDWI/NDBI).
- sar_change: For flood extent, all-weather damage, surface deformation, radar backscatter change using Sentinel-1 GRD microwave radar.
- rgb_false_color: For visual imagery inspection, false-color NIR composites.
- multispectral_fusion: For joint optical-SAR analysis.

Return ONLY a JSON object conforming strictly to this format:
{
  "pipelineKey": "optical_change" or "sar_change" or "rgb_false_color",
  "parameters": {
    "index": "NDVI",
    "threshold": 0.2,
    "cloudMask": "s2cloudless",
    "resampling": "bilinear"
  },
  "assumptions": [
    "Input scenes cover the target temporal baseline."
  ],
  "expectedOutputs": [
    "change_raster",
    "summary_statistics",
    "quality_report"
  ],
  "limitations": [
    "Spectral difference indicates physical surface alteration without establishing legal or human causality."
  ]
}
"""


class CopilotPlanner:
    """
    Synthesizes typed AnalysisPlan proposals from natural language.
    """

    @classmethod
    async def draft_plan(
        cls,
        question: str,
        mission_id: str,
        aoi_id: Optional[str] = None,
        available_assets: Optional[List[Dict[str, Any]]] = None,
        available_aois: Optional[List[Dict[str, Any]]] = None,
        user_override_pipeline: Optional[str] = None,
        context_options: Optional[Dict[str, Any]] = None,
    ) -> AnalysisPlan:
        available_assets = available_assets or []
        available_aois = available_aois or []
        context_options = context_options or {}

        q_lower = question.lower()
        cleaned = question.strip().lower()

        # Validate that the question actually contains an investigative/experimental intent
        stripped_q = cleaned.strip("!?. ")
        greetings = {
            "hello", "hi", "hey", "hola", "howdy", "good morning", "good evening",
            "test", "testing", "who are you", "what can you do", "help", "hello there",
            "hey there", "hi there", "yo", "gm", "gn", "sup", "welcome"
        }
        if stripped_q in greetings or len(stripped_q) < 5:
            raise ValueError(
                "Please specify an Earth Observation objective or question (e.g., 'Detect flood inundation', 'Measure vegetation loss', or 'Map urban expansion')."
            )

        # Step 1: Determine pipeline
        selected_pipeline_key = user_override_pipeline
        if not selected_pipeline_key:
            # Check for single-scene coverage query (e.g. water percentage, vegetation cover in AOI)
            if any(k in q_lower for k in ["percentage of water", "water present", "water percentage", "how much water", "canopy percentage", "vegetation percentage", "single scene", "coverage"]):
                selected_pipeline_key = "optical_single_index"
            # Check for AI perception / VQA queries
            elif any(k in q_lower for k in ["is there", "what is", "how many", "vqa", "visual question", "identify", "classify scene"]):
                selected_pipeline_key = "ai_vqa"
            # Check for Grounding queries
            elif any(k in q_lower for k in ["locate", "highlight", "find", "grounding", "bounding box", "show where"]):
                selected_pipeline_key = "ai_grounding"
            # Check for Siamese deep learning change
            elif any(k in q_lower for k in ["neural change", "siamese", "deep learning change", "deep change"]):
                selected_pipeline_key = "ai_neural_change"
            # Check for Hyperspectral
            elif any(k in q_lower for k in ["hyperspectral", "cube", "spectroscopy", "absorption", "hsi"]):
                selected_pipeline_key = "hyperspectral_spectroscopy"
            # Check for SAR change
            elif any(k in q_lower for k in ["sar", "radar", "microwave", "sigma0"]):
                selected_pipeline_key = "sar_change"
            # Check for Fusion
            elif any(k in q_lower for k in ["fusion", "fuse", "optical-sar", "multimodal"]):
                selected_pipeline_key = "multispectral_fusion"
            elif any(k in q_lower for k in ["rgb", "true color", "false color", "color infrared", "visual"]):
                selected_pipeline_key = "rgb_false_color"
            else:
                selected_pipeline_key = "optical_change"

        pipeline_def = PIPELINE_REGISTRY.get(selected_pipeline_key, PIPELINE_REGISTRY["optical_change"])

        # Step 2: Attempt LLM reasoning
        plan_params: Dict[str, Any] = {}
        assumptions: List[str] = []
        limitations: List[str] = []
        expected_outputs: List[str] = list(pipeline_def.outputTypes)

        try:
            from llm.gateway import llm_gateway
            prompt = (
                f"Researcher Query: '{question}'\n"
                f"Selected Pipeline: {pipeline_def.key} ({pipeline_def.label})\n"
                f"Available assets in mission: {len(available_assets)}\n"
                f"Produce standard parameters, assumptions, and scientific limitations."
            )
            response = await llm_gateway.query(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                max_tokens=600,
                temperature=0.1,
            )
            raw_text = response.text.strip()
            # Clean markdown codeblocks if returned
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()

            parsed = json.loads(raw_text)
            if isinstance(parsed, dict):
                plan_params = parsed.get("parameters", {})
                assumptions = parsed.get("assumptions", [])
                limitations = parsed.get("limitations", [])
                if parsed.get("pipelineKey") in PIPELINE_REGISTRY:
                    pipeline_def = PIPELINE_REGISTRY[parsed["pipelineKey"]]
        except Exception as exc:
            logger.info("Copilot LLM synthesis bypassed or offline (%s), using domain defaults.", exc)

        # Step 3: Ensure robust scientific parameter defaults
        if selected_pipeline_key == "optical_change":
            if not plan_params.get("index"):
                plan_params["index"] = "NDWI" if any(w in q_lower for w in ["water", "flood", "lake", "river"]) else "NDVI"
            plan_params.setdefault("threshold", 0.2)
            plan_params.setdefault("cloudMask", "s2cloudless")
            plan_params.setdefault("resampling", "bilinear")
            if not assumptions:
                assumptions = [
                    "Input Sentinel-2 scenes have undergone Sen2Cor Level-2A bottom-of-atmosphere calibration.",
                    "S2Cloudless mask threshold set to 40% to exclude contaminated atmospheric pixels.",
                ]
            if not limitations:
                limitations = [
                    "Spectral change detection indicates physical reflectance difference and does not establish human vs climatic causality.",
                ]
        elif selected_pipeline_key == "optical_single_index":
            if not plan_params.get("index"):
                plan_params["index"] = "NDWI" if any(w in q_lower for w in ["water", "flood", "lake", "river", "hydrology"]) else ("NDVI" if any(w in q_lower for w in ["vegetation", "canopy", "forest", "crop"]) else "NDBI")
            plan_params.setdefault("threshold", 0.0 if plan_params.get("index") == "NDWI" else 0.3)
            plan_params.setdefault("cloudMask", "s2cloudless")
            if not assumptions:
                assumptions = [
                    f"Calibrated single-scene surface reflectance used to evaluate {plan_params['index']} coverage inside AOI.",
                ]
            if not limitations:
                limitations = [
                    "Threshold classification reflects surface state at acquisition time and is sensitive to cloud shadows.",
                ]
        elif selected_pipeline_key == "ai_vqa":
            plan_params.setdefault("confidenceThreshold", 0.5)
            if not assumptions:
                assumptions = ["Neural VQA model trained on multimodal remote-sensing classification dataset."]
            if not limitations:
                limitations = ["Answer vocabulary is constrained by trained domain ontology."]
        elif selected_pipeline_key == "ai_grounding":
            plan_params.setdefault("minConfidence", 0.35)
            plan_params.setdefault("nmsThreshold", 0.45)
            if not assumptions:
                assumptions = ["Spatial region grounding parses semantic query to bounding box contours."]
        elif selected_pipeline_key == "ai_neural_change":
            plan_params.setdefault("probabilityThreshold", 0.5)
            if not assumptions:
                assumptions = ["Siamese bi-temporal differential net compares learned spatial feature representations."]
        elif selected_pipeline_key == "sar_change":
            plan_params.setdefault("polarization", "VV")
            plan_params.setdefault("thresholdDb", -3.0)
            plan_params.setdefault("resampling", "bilinear")
            if not assumptions:
                assumptions = [
                    "Sentinel-1 GRD products acquired on same relative orbit pass geometry to prevent look-angle distortion.",
                ]
            if not limitations:
                limitations = [
                    "SAR backscatter variation may be influenced by transient soil moisture changes or surface roughness rather than permanent structure removal.",
                ]
        elif selected_pipeline_key == "rgb_false_color":
            plan_params.setdefault("composition", "ColorInfrared_NIR_R_G" if "nir" in q_lower or "vegetation" in q_lower else "TrueColor_RGB")
            plan_params.setdefault("resampling", "bilinear")
            plan_params.setdefault("stretch", "2_percent_linear")
            if not assumptions:
                assumptions = ["Radiometric stretch calculated across valid cloud-free pixels."]
            if not limitations:
                limitations = ["Visual false-color rendering is qualitative for analyst inspection."]

        # If user explicitly specified parameters via Experiment Setup, override defaults
        if context_options.get("parameters") and isinstance(context_options["parameters"], dict):
            plan_params.update(context_options["parameters"])

        # Step 4: Resolve input bindings
        inputs: List[AnalysisPlanInputBinding] = []
        is_bitemporal = pipeline_def.key in ["optical_change", "sar_change", "ai_neural_change", "multispectral_fusion"]

        if is_bitemporal:
            # Needs before_scene and after_scene
            req_before_id = context_options.get("before_asset_id")
            req_after_id = context_options.get("after_asset_id")

            before_ast = next((a for a in available_assets if a.get("id") == req_before_id), None) if req_before_id else None
            after_ast = next((a for a in available_assets if a.get("id") == req_after_id), None) if req_after_id else None

            if not before_ast and available_assets:
                before_ast = available_assets[0]
            if not after_ast and len(available_assets) > 1:
                after_ast = available_assets[1]

            before_title = (
                (before_ast.get("title") or before_ast.get("external_id") or "Baseline Reference Acquisition (T0)")
                if before_ast
                else "Baseline Reference Acquisition (T0)"
            )
            after_title = (
                (after_ast.get("title") or after_ast.get("external_id") or "Target Event Acquisition (T1)")
                if after_ast
                else "Target Event Acquisition (T1)"
            )

            inputs.append(
                AnalysisPlanInputBinding(
                    role="before_scene",
                    assetVersionId=before_ast["versions"][0]["id"]
                    if before_ast and before_ast.get("versions")
                    else f"ast_v_{mission_id}_t0",
                    assetId=before_ast["id"] if before_ast else f"ast_{mission_id}_t0",
                    label=before_title,
                )
            )
            inputs.append(
                AnalysisPlanInputBinding(
                    role="after_scene",
                    assetVersionId=after_ast["versions"][0]["id"]
                    if after_ast and after_ast.get("versions")
                    else f"ast_v_{mission_id}_t1",
                    assetId=after_ast["id"] if after_ast else f"ast_{mission_id}_t1",
                    label=after_title,
                )
            )
        else:
            # Single-scene mode (optical_single_index, ai_vqa, ai_grounding, rgb_false_color, hyperspectral)
            req_target_id = context_options.get("target_asset_id") or context_options.get("before_asset_id")
            target_ast = next((a for a in available_assets if a.get("id") == req_target_id), None) if req_target_id else None
            if not target_ast and available_assets:
                target_ast = available_assets[0]

            src_title = (
                (target_ast.get("title") or target_ast.get("external_id") or "Target Observation Scene")
                if target_ast
                else "Target Observation Scene"
            )
            inputs.append(
                AnalysisPlanInputBinding(
                    role="target_scene",
                    assetVersionId=target_ast["versions"][0]["id"]
                    if target_ast and target_ast.get("versions")
                    else f"ast_v_{mission_id}_target",
                    assetId=target_ast["id"] if target_ast else f"ast_{mission_id}_target",
                    label=src_title,
                )
            )

        if aoi_id:
            inputs.append(
                AnalysisPlanInputBinding(
                    role="optional_mask",
                    assetVersionId=f"mask_{aoi_id}",
                    label="AOI Vector Boundary Mask",
                )
            )

        # Step 5: Time range
        now = datetime.utcnow()
        time_range = {
            "before": {
                "start": (now - timedelta(days=60)).strftime("%Y-%m-%d"),
                "end": (now - timedelta(days=30)).strftime("%Y-%m-%d"),
            },
            "after": {
                "start": (now - timedelta(days=15)).strftime("%Y-%m-%d"),
                "end": now.strftime("%Y-%m-%d"),
            },
        }

        # Step 6: Assemble Plan
        plan = AnalysisPlan(
            missionId=mission_id,
            questionText=question,
            aoiId=aoi_id,
            pipeline=AnalysisPlanPipelineRef(
                key=pipeline_def.key,
                version=pipeline_def.version,
                label=pipeline_def.label,
            ),
            inputs=inputs,
            timeRange=time_range,
            parameters=plan_params,
            assumptions=assumptions,
            expectedOutputs=expected_outputs,
            limitations=limitations,
            status=PlanStatus.DRAFT,
        )

        # Step 7: Perform domain validation
        blocking_errors, warnings = PlanDomainValidator.validate_plan(plan, available_assets, available_aois)
        plan.blockingErrors = blocking_errors
        plan.warnings = warnings
        if not blocking_errors:
            plan.status = PlanStatus.VALIDATED

        return plan
