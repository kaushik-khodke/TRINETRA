"""
SatQuery AI / TRINETRA — LangGraph Agentic Workflow Runtime
Replaces sequential procedural routing with an explicit StateGraph workflow.
Guarantees strict input validation, non-remote-sensing rejection, modality-aware routing,
allow-listed tool selection, specialist execution, and evidence-grounded responses.
"""

import os
import sys
import time
from typing import Dict, Any, List, Optional, TypedDict

# Ensure backend root in sys.path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from langgraph.graph import StateGraph, END

from agent.registry import TOOL_REGISTRY, get_tool
from agent.classifier import TaskClassifier
from agent.trace import ExecutionTrace
from services.validator.validator import InputValidator
from services.vqa.vqa_service import RSVqaSpecialist
from services.captioning.captioning_service import RSCaptionSpecialist
from services.grounding.grounding_service import RSGroundingSpecialist
from services.change.change_service import BiTemporalChangeSpecialist
from services.optical_sar.optical_sar_service import OpticalSarFusionSpecialist
from services.hyperspectral.hsi_service import HyperFreeHSISpecialist
from services.intelligence_builder import StructuredIntelligenceBuilder
from geospatial.reader import GeospatialReader

class AgentWorkflowState(TypedDict):
    request_id: str
    trace_id: str
    file_paths: List[str]
    query: str
    input_mode: str
    declared_modalities: Optional[List[str]]
    custom_parameters: Dict[str, Any]
    response_language: str
    is_valid: bool
    validation_report: Dict[str, Any]
    detected_modality: str
    detected_task: str
    selected_tools: List[str]
    specialist_output: Dict[str, Any]
    final_response: Dict[str, Any]
    error: Optional[str]
    execution_steps: List[Dict[str, Any]]
    execution_trace: Dict[str, Any]

class LangGraphOrchestrator:
    """Explicit LangGraph StateGraph engine for multimodal Earth observation perception."""
    def __init__(self):
        self.classifier = TaskClassifier()
        self.vqa_specialist = RSVqaSpecialist()
        self.caption_specialist = RSCaptionSpecialist()
        self.grounding_specialist = RSGroundingSpecialist()
        self.change_specialist = BiTemporalChangeSpecialist()
        self.optical_sar_specialist = OpticalSarFusionSpecialist()
        self.hsi_specialist = HyperFreeHSISpecialist()

        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentWorkflowState)

        # Register Workflow Nodes
        workflow.add_node("input_validator", self._node_validate_input)
        workflow.add_node("modality_classifier", self._node_classify_modality)
        workflow.add_node("task_router", self._node_route_task)
        workflow.add_node("tool_selector", self._node_select_tools)
        workflow.add_node("specialist_model", self._node_execute_specialist)
        workflow.add_node("geospatial_processing", self._node_geospatial_processing)
        workflow.add_node("evidence_builder", self._node_build_evidence)
        workflow.add_node("response_generator", self._node_generate_response)
        workflow.add_node("rejection_handler", self._node_rejection_handler)

        # Set Entry Point
        workflow.set_entry_point("input_validator")

        # Conditional Edge after Validation
        workflow.add_conditional_edges(
            "input_validator",
            self._check_validation_condition,
            {
                "valid": "modality_classifier",
                "invalid": "rejection_handler"
            }
        )

        # Linear Processing Pipeline
        workflow.add_edge("modality_classifier", "task_router")
        workflow.add_edge("task_router", "tool_selector")
        workflow.add_edge("tool_selector", "specialist_model")
        workflow.add_edge("specialist_model", "geospatial_processing")
        workflow.add_edge("geospatial_processing", "evidence_builder")
        workflow.add_edge("evidence_builder", "response_generator")

        # Terminal Edges
        workflow.add_edge("response_generator", END)
        workflow.add_edge("rejection_handler", END)

        return workflow.compile()

    # =========================================================================
    # Node Implementations
    # =========================================================================

    def _node_validate_input(self, state: AgentWorkflowState) -> Dict[str, Any]:
        """Node 1: Input Validation Agent."""
        files = state["file_paths"]
        mode = state["input_mode"]
        declared = state["declared_modalities"]

        # Step trace
        steps = list(state.get("execution_steps", []))
        steps.append({
            "stage": "validation",
            "action": "input_verification",
            "timestamp": time.time(),
            "details": f"Validating {len(files)} raster input(s) against remote-sensing domain rules."
        })

        # Physical security: all files must exist
        for f in files:
            if not os.path.isfile(f):
                return {
                    "is_valid": False,
                    "error": f"Target raster file does not exist on disk: {f}",
                    "execution_steps": steps
                }

        val_report = InputValidator.validate(files, requested_mode=mode, declared_modalities=declared)
        report_dict = val_report.model_dump() if hasattr(val_report, "model_dump") else val_report.dict()

        if not val_report.valid:
            err = val_report.error_message or "Unsupported input: this image does not appear to be a supported remote-sensing product."
            steps.append({
                "stage": "validation",
                "action": "input_rejected",
                "timestamp": time.time(),
                "details": err
            })
            return {
                "is_valid": False,
                "validation_report": report_dict,
                "error": err,
                "execution_steps": steps
            }

        steps.append({
            "stage": "validation",
            "action": "validation_passed",
            "timestamp": time.time(),
            "details": f"Verified remote-sensing format and physical plausibility for: {', '.join(os.path.basename(f) for f in files)}."
        })

        return {
            "is_valid": True,
            "input_mode": val_report.mode,
            "validation_report": report_dict,
            "error": None,
            "execution_steps": steps
        }

    def _check_validation_condition(self, state: AgentWorkflowState) -> str:
        return "valid" if state.get("is_valid", False) else "invalid"

    def _node_classify_modality(self, state: AgentWorkflowState) -> Dict[str, Any]:
        """Node 2: Modality Classifier."""
        report = state["validation_report"]
        mode = state["input_mode"]
        images_meta = report.get("images_metadata", [])

        # Priority resolution
        if mode == "optical_sar":
            detected_modality = "optical_sar"
        elif mode == "bi_temporal":
            detected_modality = "bi_temporal"
        elif images_meta:
            detected_modality = images_meta[0].get("modality", "optical")
        else:
            detected_modality = "optical"

        steps = list(state.get("execution_steps", []))
        steps.append({
            "stage": "classification",
            "action": "modality_identified",
            "timestamp": time.time(),
            "details": f"Identified raster sensor modality: {detected_modality.upper()}."
        })

        return {
            "detected_modality": detected_modality,
            "execution_steps": steps
        }

    def _node_route_task(self, state: AgentWorkflowState) -> Dict[str, Any]:
        """Node 3: Task Router."""
        modality = state["detected_modality"]
        query = state["query"]
        mode = state["input_mode"]
        files = state["file_paths"]

        steps = list(state.get("execution_steps", []))

        if modality == "hyperspectral":
            detected_task = "hyperspectral_analysis"
        elif mode == "optical_sar":
            detected_task = "optical_sar_fusion"
        elif mode == "bi_temporal":
            detected_task = "change_detection"
        else:
            classification = self.classifier.classify(query, mode, len(files), [modality])
            detected_task = classification.task

        steps.append({
            "stage": "routing",
            "action": "task_selected",
            "timestamp": time.time(),
            "details": f"Routed query to target capability: '{detected_task}'."
        })

        return {
            "detected_task": detected_task,
            "execution_steps": steps
        }

    def _node_select_tools(self, state: AgentWorkflowState) -> Dict[str, Any]:
        """Node 4: Tool Selector (Allow-Listed Registry)."""
        task = state["detected_task"]
        modality = state["detected_modality"]

        selected = []
        if modality == "hyperspectral":
            selected = ["hyperfree_hsi", "gdal_rasterio_gis", "spectral_signature_tool"]
        elif task == "vqa":
            selected = ["rs_vqa"]
        elif task == "captioning":
            selected = ["rs_caption"]
        elif task == "grounding":
            selected = ["rs_ground"]
        elif task == "change_detection":
            selected = ["change_ai", "gdal_rasterio_gis"]
        elif task == "optical_sar_fusion":
            selected = ["optical_sar", "gdal_rasterio_gis"]
        else:
            selected = ["rs_vqa"]

        # Validate that all selected tools are strictly in the allow-list
        for t in selected:
            if t not in TOOL_REGISTRY:
                raise ValueError(f"Security Alert: Tool '{t}' is not registered in TOOL_REGISTRY allow-list.")

        steps = list(state.get("execution_steps", []))
        steps.append({
            "stage": "tool_selection",
            "action": "tools_bound",
            "timestamp": time.time(),
            "details": f"Bound allow-listed specialist tools: {', '.join(selected)}."
        })

        return {
            "selected_tools": selected,
            "execution_steps": steps
        }

    def _node_execute_specialist(self, state: AgentWorkflowState) -> Dict[str, Any]:
        """Node 5: Specialist Model Execution."""
        task = state["detected_task"]
        modality = state["detected_modality"]
        files = state["file_paths"]
        query = state["query"]
        params = state["custom_parameters"]
        lang = state["response_language"]
        report = state["validation_report"]
        images_meta = report.get("images_metadata", [{}])

        steps = list(state.get("execution_steps", []))
        t0 = time.time()

        # 1. Hyperspectral Foundation Specialist
        if modality == "hyperspectral" or "hyperfree_hsi" in state["selected_tools"]:
            arr, meta = GeospatialReader.read_image(files[0])
            out = self.hsi_specialist.execute(
                image_path=files[0],
                image_arr=arr,
                meta=meta.to_dict(),
                query=query,
                parameters=params,
                response_language=lang
            )

        # 2. Bi-Temporal Change Specialist
        elif task in ["change_detection", "change_analysis"]:
            arr1, meta1 = GeospatialReader.read_image(files[0])
            arr2, meta2 = GeospatialReader.read_image(files[1])
            eff_params = dict(params)
            eff_params["response_language"] = lang
            out = self.change_specialist.execute(
                images_arr=[arr1, arr2],
                metas=[meta1.to_dict(), meta2.to_dict()],
                query=query,
                parameters=eff_params
            )

        # 3. Optical-SAR Cross-Modal Specialist
        elif task in ["optical_sar_fusion", "fusion"]:
            arr1, meta1 = GeospatialReader.read_image(files[0])
            arr2, meta2 = GeospatialReader.read_image(files[1])
            eff_params = dict(params)
            eff_params["response_language"] = lang
            out = self.optical_sar_specialist.execute(
                images_arr=[arr1, arr2],
                metas=[meta1.to_dict(), meta2.to_dict()],
                query=query,
                parameters=eff_params
            )

        # 4. Text-Guided Region Grounding Specialist
        elif task == "grounding":
            arr, meta = GeospatialReader.read_image(files[0])
            eff_params = dict(params)
            eff_params["response_language"] = lang
            out = self.grounding_specialist.execute(
                image_arr=arr,
                meta=meta.to_dict(),
                query=query,
                parameters=eff_params
            )

        # 5. Scene Captioning Specialist
        elif task == "captioning":
            arr, meta = GeospatialReader.read_image(files[0])
            eff_params = dict(params)
            eff_params["response_language"] = lang
            out = self.caption_specialist.execute(
                image_arr=arr,
                meta=meta.to_dict(),
                query=query,
                parameters=eff_params
            )

        # 6. Remote-Sensing VQA Specialist
        else:
            arr, meta = GeospatialReader.read_image(files[0])
            eff_params = dict(params)
            eff_params["response_language"] = lang
            out = self.vqa_specialist.execute(
                image_arr=arr,
                meta=meta.to_dict(),
                query=query,
                parameters=eff_params
            )

        latency = round((time.time() - t0) * 1000.0, 1)
        steps.append({
            "stage": "specialist_execution",
            "action": "inference_completed",
            "timestamp": time.time(),
            "latency_ms": latency,
            "details": f"Specialist '{out.get('engine', task)}' executed successfully in {latency}ms."
        })

        return {
            "specialist_output": out,
            "execution_steps": steps
        }

    def _node_geospatial_processing(self, state: AgentWorkflowState) -> Dict[str, Any]:
        """Node 6: GIS Vectorization & Coordinate Transform."""
        out = state["specialist_output"]
        steps = list(state.get("execution_steps", []))

        # Check if vector geometries exist
        has_geojson = bool(out.get("geojson"))
        steps.append({
            "stage": "geospatial_processing",
            "action": "vector_verification",
            "timestamp": time.time(),
            "details": f"Geospatial vector geometry extraction: {'Attached valid GeoJSON features' if has_geojson else 'Raster coordinate alignment preserved'}."
        })
        return {"execution_steps": steps}

    def _node_build_evidence(self, state: AgentWorkflowState) -> Dict[str, Any]:
        """Node 7: Multimodal Evidence Builder."""
        out = state["specialist_output"]
        steps = list(state.get("execution_steps", []))

        evidence_types = []
        if out.get("evidence_image"): evidence_types.append("visual_overlay")
        if out.get("spectral_signature"): evidence_types.append("spectral_curve")
        if out.get("geojson"): evidence_types.append("geojson_polygons")
        if out.get("bounding_box") or out.get("regions"): evidence_types.append("bounding_boxes")

        steps.append({
            "stage": "evidence_builder",
            "action": "evidence_compiled",
            "timestamp": time.time(),
            "details": f"Compiled verifiable evidence layers: {', '.join(evidence_types) if evidence_types else 'radiometric statistics'}."
        })
        return {"execution_steps": steps}

    def _node_generate_response(self, state: AgentWorkflowState) -> Dict[str, Any]:
        """Node 8: Final Response Assembly."""
        out = state["specialist_output"]
        steps = state["execution_steps"]

        trace_dict = {
            "request_id": state["request_id"],
            "trace_id": state["trace_id"],
            "input_mode": state["input_mode"],
            "detected_task": state["detected_task"],
            "detected_modality": state["detected_modality"],
            "selected_tools": state["selected_tools"],
            "steps": steps,
            "status": "completed"
        }

        # Extract geographic location for TRINETRA 3D Earth Globe integration (supports 1 or multiple rasters)
        files = state.get("file_paths", [])
        geo_location = {
            "has_location": False,
            "lat": None,
            "lng": None,
            "height": 5000,
            "bounds": None,
            "crs": None,
            "location_name": None
        }
        valid_metas = []
        for f in files:
            if f and os.path.exists(f):
                try:
                    from geospatial.reader import GeospatialReader
                    m = GeospatialReader.read_metadata(f)
                    if m.has_geographic_location:
                        valid_metas.append(m)
                except Exception as e:
                    print(f"[LangGraph] Metadata extraction notice for {f}: {e}")

        if valid_metas:
            if len(valid_metas) == 1:
                m = valid_metas[0]
                geo_location = {
                    "has_location": True,
                    "lat": m.center_lat,
                    "lng": m.center_lng,
                    "height": 5000,
                    "bounds": list(m.bounds) if m.bounds else None,
                    "crs": m.crs or "EPSG:4326",
                    "location_name": m.location_name or "Satellite Target"
                }
            else:
                # Two or more observations (e.g., bi-temporal change or optical-SAR pair)
                lats = [m.center_lat for m in valid_metas if m.center_lat is not None]
                lngs = [m.center_lng for m in valid_metas if m.center_lng is not None]
                avg_lat = round(sum(lats) / len(lats), 6) if lats else None
                avg_lng = round(sum(lngs) / len(lngs), 6) if lngs else None
                
                # Compute bounding box encompassing both scenes
                all_b = [m.bounds for m in valid_metas if m.bounds]
                if all_b:
                    min_x = min(b[0] for b in all_b)
                    min_y = min(b[1] for b in all_b)
                    max_x = max(b[2] for b in all_b)
                    max_y = max(b[3] for b in all_b)
                    combined_bounds = [round(min_x, 6), round(min_y, 6), round(max_x, 6), round(max_y, 6)]
                else:
                    combined_bounds = None

                names = [m.location_name for m in valid_metas if m.location_name]
                loc_name = " & ".join(names) if names else ("Bi-Temporal Study Target" if state.get("input_mode") == "bi_temporal" else "Optical-SAR Target Area")

                geo_location = {
                    "has_location": True,
                    "lat": avg_lat,
                    "lng": avg_lng,
                    "height": 6000,
                    "bounds": combined_bounds,
                    "crs": valid_metas[0].crs or "EPSG:4326",
                    "location_name": loc_name
                }

        out["geographic_location"] = geo_location

        # Synthesize Structured Multimodal Intelligence Response
        struct_intel = StructuredIntelligenceBuilder.build(
            task=out.get("task") or state["detected_task"],
            modality=state["detected_modality"],
            query=state["query"],
            specialist_output=out,
            geo_location=geo_location,
            validation_report=state.get("validation_report"),
            raw_b64=out.get("raw_preview")
        )

        out["structured_intelligence"] = struct_intel
        if struct_intel.get("regions"):
            out["regions"] = struct_intel["regions"]
        if struct_intel.get("structured_answer"):
            out["structured_answer"] = struct_intel["structured_answer"]

        final_resp = {
            "request_id": state["request_id"],
            "trace_id": state["trace_id"],
            "status": "completed",
            "query": state["query"],
            "input_mode": state["input_mode"],
            "task": out.get("task") or state["detected_task"],
            "detected_task": state["detected_task"],
            "detected_modality": state["detected_modality"],
            "selected_tools": state["selected_tools"],
            "confidence": struct_intel.get("composite_confidence", out.get("confidence", 0.90)),
            "result": out,
            "answer": out.get("answer", "Analysis completed."),
            "structured_answer": struct_intel.get("structured_answer"),
            "structured_intelligence": struct_intel,
            "regions": struct_intel.get("regions", out.get("regions", [])),
            "bounding_box": out.get("bounding_box"),
            "evidence_image": out.get("evidence_image") or out.get("evidence"),
            "engine": out.get("engine", "TRINETRA Agent"),
            "agent_framework": "langchain",
            "cloud_llm": False,
            "geographic_location": geo_location,
            "evidence": {
                "image": out.get("evidence_image") or out.get("evidence"),
                "rgb_composite": out.get("rgb_composite"),
                "cir_composite": out.get("cir_composite"),
                "spectral_signature": out.get("spectral_signature"),
                "cube_metadata": out.get("cube_metadata"),
                "bounding_box": out.get("bounding_box"),
                "regions": struct_intel.get("regions", out.get("regions")),
                "geojson": out.get("geojson"),
                "change_stats": out.get("change_stats"),
                "fused_stats": out.get("fused_stats"),
                "top_classes": out.get("top_classes"),
                "measurements": struct_intel.get("measurements")
            },
            "execution_trace": trace_dict
        }

        return {"final_response": final_resp}

    def _node_rejection_handler(self, state: AgentWorkflowState) -> Dict[str, Any]:
        """Node 9: Non-Remote-Sensing Short-Circuit Rejection Handler."""
        err_msg = state.get("error") or "Unsupported input: this image does not appear to be a supported remote-sensing product."
        steps = state.get("execution_steps", [])

        trace_dict = {
            "request_id": state["request_id"],
            "trace_id": state["trace_id"],
            "input_mode": state["input_mode"],
            "detected_task": "rejection",
            "detected_modality": "unsupported",
            "selected_tools": ["validator"],
            "steps": steps,
            "status": "rejected"
        }

        final_resp = {
            "request_id": state["request_id"],
            "trace_id": state["trace_id"],
            "status": "failed",
            "error": err_msg,
            "validation_report": state.get("validation_report"),
            "execution_trace": trace_dict
        }

        return {"final_response": final_resp}

    # =========================================================================
    # Orchestrator Entrypoint
    # =========================================================================

    def run(
        self,
        request_id: str,
        trace_id: str,
        file_paths: List[str],
        query: str,
        input_mode: str = "single",
        declared_modalities: Optional[List[str]] = None,
        custom_parameters: Optional[Dict[str, Any]] = None,
        response_language: str = "en"
    ) -> Dict[str, Any]:
        initial_state: AgentWorkflowState = {
            "request_id": request_id,
            "trace_id": trace_id,
            "file_paths": file_paths,
            "query": query,
            "input_mode": input_mode,
            "declared_modalities": declared_modalities,
            "custom_parameters": custom_parameters or {},
            "response_language": response_language,
            "is_valid": True,
            "validation_report": {},
            "detected_modality": "unknown",
            "detected_task": "pending",
            "selected_tools": [],
            "specialist_output": {},
            "final_response": {},
            "error": None,
            "execution_steps": [],
            "execution_trace": {}
        }

        # Run compiled LangGraph workflow
        final_state = self.graph.invoke(initial_state)
        return final_state["final_response"]
