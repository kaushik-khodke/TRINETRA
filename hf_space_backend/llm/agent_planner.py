"""
SatQuery AI — LangChain-Powered Multi-Step Agent Planner
Deconstructs complex natural-language remote-sensing queries into typed,
executable tool sequences with strict schema validation.
"""

from typing import List, Dict, Any, Optional
from llm.ollama_provider import OllamaProvider
from llm.model_registry import LocalModelRegistry
from llm.schemas import ExecutionPlan, PlanStep, IntentPlan

class AgentPlanner:
    """Plans and decomposes remote-sensing workflows."""

    @classmethod
    def plan(
        cls,
        query: str,
        input_mode: str,
        num_images: int,
        image_modalities: List[str]
    ) -> ExecutionPlan:
        """
        Creates an observable, structured execution plan for a user query.
        Uses fast local model (qwen3.5:4b) or planner model (qwen3.5:9b) for complex queries,
        with deterministic semantic fallback.
        """
        clean_q = query.lower()
        complexity = "complex" if any(w in clean_q for w in ["also", "then", "compare", "calculate", "decrease", "expand"]) else "simple"
        role = "fast_router"
        model_tag, available = LocalModelRegistry.resolve_model_for_role(role)

        # 1. Deterministic Semantic Task Inference (Instant, Zero Hallucination, 100% Air-Gapped)
        task, reasoning = cls._deterministic_task_inference(clean_q, input_mode, num_images, image_modalities)
        steps = cls._build_steps_for_intent(task, input_mode, clean_q)

        return ExecutionPlan(
            query=query,
            complexity=complexity,
            task=task,
            selected_model_role=role,
            selected_model_tag=model_tag,
            steps=steps,
            reasoning=reasoning
        )

    @staticmethod
    def _deterministic_task_inference(query: str, mode: str, count: int, modalities: List[str]) -> (str, str):
        if mode == "optical_sar" or (count == 2 and any(m == "sar" for m in modalities) and any(m == "optical" for m in modalities)):
            return "optical_sar_fusion", "Cross-modal query combining Optical spectral bands with SAR microwave backscatter."
        
        if mode == "bi_temporal" or (count == 2 and any(w in query for w in ["change", "dates", "between", "difference", "increase", "decrease", "expanded"])):
            return "change_analysis", "Bi-temporal change detection comparing baseline T1 against monitoring T2 observation."

        if any(w in query for w in ["highlight", "locate", "segment", "find", "show me where", "boundary", "box"]):
            return "grounding", "Text-guided spatial region localization and bounding contour extraction."

        if any(w in query for w in ["describe", "caption", "overview", "summary", "composition", "scene"]):
            return "captioning", "Broad scene description and multi-class land-cover composition synthesis."

        return "vqa", "Specific visual question answering grounded in radiometric surface features."

    @staticmethod
    def _build_steps_for_intent(task: str, mode: str, query: str) -> List[PlanStep]:
        steps = [
            PlanStep(
                step_id=1,
                tool_name="validator",
                action="validate_inputs",
                parameters={"input_mode": mode},
                objective="Verify file readability, dimensions, band counts, CRS, and pair alignment."
            )
        ]

        if task == "change_analysis":
            steps.append(PlanStep(
                step_id=2,
                tool_name="change_ai",
                action="compute_differential_change",
                parameters={"threshold": 0.25},
                objective="Calculate absolute pixel difference matrix, quadrant breakdown, and shift trends."
            ))
            steps.append(PlanStep(
                step_id=3,
                tool_name="evidence_engine",
                action="render_change_heatmap",
                parameters={"colormap": "solar_amber"},
                objective="Generate visual Solar Amber change overlay indicating altered parcels."
            ))

        elif task == "optical_sar_fusion":
            steps.append(PlanStep(
                step_id=2,
                tool_name="optical_sar",
                action="fuse_cross_modal_features",
                parameters={"sar_threshold_db": -8.0},
                objective="Cross-reference optical NDVI/NDWI against SAR double-bounce and specular backscatter."
            ))
            steps.append(PlanStep(
                step_id=3,
                tool_name="evidence_engine",
                action="render_composite",
                parameters={"blend_ratio": 0.5},
                objective="Generate fused visual composite highlighting structural concordance."
            ))

        elif task == "grounding":
            steps.append(PlanStep(
                step_id=2,
                tool_name="rs_ground",
                action="detect_target_contours",
                parameters={"query": query},
                objective="Isolate requested spatial features and calculate normalized bounding coordinates."
            ))
            steps.append(PlanStep(
                step_id=3,
                tool_name="evidence_engine",
                action="render_bounding_boxes",
                parameters={"box_color": "#10B981"},
                objective="Draw tactical bounding boxes and confidence tags over raw raster."
            ))

        elif task == "captioning":
            steps.append(PlanStep(
                step_id=2,
                tool_name="rs_caption",
                action="extract_scene_composition",
                parameters={},
                objective="Compute multi-spectral land-cover breakdown and summarize dominant landscape features."
            ))

        else:  # vqa
            steps.append(PlanStep(
                step_id=2,
                tool_name="rs_vqa",
                action="query_surface_features",
                parameters={"query": query},
                objective="Extract spectral vegetation, water, and built-up indices to answer user question."
            ))

        steps.append(PlanStep(
            step_id=len(steps) + 1,
            tool_name="local_llm_synthesis",
            action="synthesize_grounded_answer",
            parameters={"model_role": "planner"},
            objective="Formulate natural-language response strictly citing computed physical metrics."
        ))

        return steps
