"""
SatQuery AI — Master Agent Controller
The central orchestration layer. Routes requests, validates inputs, sequences specialist tools,
integrates multimodal evidence, and logs observable execution traces.
"""

import os
import sys
import time

# Ensure backend root is always in sys.path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from typing import List, Dict, Any, Optional
from agent.registry import TOOL_REGISTRY, get_tool
from agent.classifier import TaskClassifier
from agent.trace import ExecutionTrace
from services.validator.validator import InputValidator
from services.vqa.vqa_service import RSVqaSpecialist
from services.captioning.captioning_service import RSCaptionSpecialist
from services.grounding.grounding_service import RSGroundingSpecialist
from services.change.change_service import BiTemporalChangeSpecialist
from services.optical_sar.optical_sar_service import OpticalSarFusionSpecialist
from services.reports.report_service import MissionReportGenerator
from geospatial.reader import GeospatialReader
from geospatial.overlays import EvidenceOverlayEngine

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

class AgentController:
    def __init__(self):
        self.classifier = TaskClassifier()
        self.vqa_specialist = RSVqaSpecialist()
        self.caption_specialist = RSCaptionSpecialist()
        self.grounding_specialist = RSGroundingSpecialist()
        self.change_specialist = BiTemporalChangeSpecialist()
        self.optical_sar_specialist = OpticalSarFusionSpecialist()

    def process_request(
        self,
        file_paths: List[str],
        query: str,
        input_mode: str = "single",
        declared_modalities: Optional[List[str]] = None,
        custom_parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        trace = ExecutionTrace(
            input_mode=input_mode,
            query=query,
            detected_task="pending"
        )
        t0 = time.time()

        # Step 1: Input Validation
        trace.add_step(
            stage="validation",
            action="inspect_inputs",
            tool="validator",
            details=f"Validating {len(file_paths)} input raster(s) for mode '{input_mode}'."
        )

        val_report = InputValidator.validate(file_paths, requested_mode=input_mode, declared_modalities=declared_modalities)
        if not val_report.valid:
            trace.fail(val_report.error_message or "Input validation failed.")
            dump = trace.model_dump() if hasattr(trace, "model_dump") else trace.dict()
            return {
                "request_id": trace.request_id,
                "status": "failed",
                "error": val_report.error_message,
                "execution_trace": dump
            }

        trace.add_step(
            stage="validation",
            action="validation_passed",
            tool="validator",
            details=f"All files verified: {', '.join(os.path.basename(p) for p in file_paths)}."
        )

        # Step 2: Task Classification
        num_images = len(file_paths)
        image_modalities = [m["modality"] for m in val_report.images_metadata]
        classification = self.classifier.classify(query, input_mode, num_images, image_modalities)
        trace.detected_task = classification.task

        trace.add_step(
            stage="classification",
            action="classify_intent",
            details=f"Task classified as '{classification.task}' with confidence {classification.confidence}. Reasoning: {classification.reasoning}"
        )

        # Step 3: Tool Selection & Parameter Configuration
        target_tool_id = classification.recommended_tools[1] if len(classification.recommended_tools) > 1 else "rs_vqa"
        tool_meta = get_tool(target_tool_id)

        permitted_params = tool_meta.permitted_parameters.copy()
        if custom_parameters:
            for k, v in custom_parameters.items():
                if k in permitted_params:
                    permitted_params[k] = v

        trace.selected_tools = [
            {"name": "validator", "version": "1.2.0"},
            {"name": tool_meta.name, "version": tool_meta.version}
        ]
        trace.parameters = permitted_params

        trace.add_step(
            stage="planning",
            action="select_specialist_tool",
            tool=tool_meta.tool_id,
            parameters=permitted_params,
            details=f"Selected tool '{tool_meta.name}' [{tool_meta.version}]. Configured permitted parameters."
        )

        # Step 4: Raster Ingestion
        loaded_arrays = []
        loaded_metas = []
        image_previews = []
        for i, path in enumerate(file_paths):
            arr, meta = GeospatialReader.read_image(path, detected_modality=image_modalities[i])
            loaded_arrays.append(arr)
            loaded_metas.append(meta.to_dict())
            rgb_preview = GeospatialReader.to_rgb_preview(arr, image_modalities[i])
            image_previews.append(EvidenceOverlayEngine.to_base64(rgb_preview))

        # Step 5: Execute Specialist Workflow
        trace.add_step(
            stage="execution",
            action="run_inference",
            tool=tool_meta.tool_id,
            details=f"Invoking {tool_meta.name} with inputs."
        )

        try:
            if classification.task == "optical_sar_fusion":
                result = self.optical_sar_specialist.execute(
                    images_arr=loaded_arrays,
                    metas=loaded_metas,
                    query=query,
                    parameters=permitted_params
                )
            elif classification.task == "change_analysis":
                result = self.change_specialist.execute(
                    images_arr=loaded_arrays,
                    metas=loaded_metas,
                    query=query,
                    parameters=permitted_params
                )
            elif classification.task == "grounding":
                result = self.grounding_specialist.execute(
                    image_arr=loaded_arrays[0],
                    meta=loaded_metas[0],
                    query=query,
                    parameters=permitted_params
                )
            elif classification.task == "captioning":
                result = self.caption_specialist.execute(
                    image_arr=loaded_arrays[0],
                    meta=loaded_metas[0],
                    query=query,
                    parameters=permitted_params
                )
            else:  # default vqa
                result = self.vqa_specialist.execute(
                    image_arr=loaded_arrays[0],
                    meta=loaded_metas[0],
                    query=query,
                    parameters=permitted_params
                )

            trace.add_step(
                stage="integration",
                action="integrate_evidence",
                tool=tool_meta.tool_id,
                details="Integrated textual conclusions, visual evidence overlays, and confidence metrics."
            )

        except Exception as e:
            trace.fail(f"Specialist tool execution error: {str(e)}")
            dump = trace.model_dump() if hasattr(trace, "model_dump") else trace.dict()
            return {
                "request_id": trace.request_id,
                "status": "failed",
                "error": str(e),
                "execution_trace": dump
            }

        # Step 6: Generate Downloadable Report Files
        report_html_filename = f"report_{trace.request_id[:8]}.html"
        report_json_filename = f"report_{trace.request_id[:8]}.json"
        html_path = os.path.join(REPORTS_DIR, report_html_filename)
        json_path = os.path.join(REPORTS_DIR, report_json_filename)

        # Determine primary geographic location from verified raster inputs
        primary_geo = None
        for m in loaded_metas:
            if m.get("has_geographic_location") and m.get("center_lat") is not None:
                primary_geo = {
                    "has_location": True,
                    "lat": m["center_lat"],
                    "lng": m["center_lng"],
                    "height": 5000,
                    "bounds": m.get("bounds"),
                    "crs": m.get("crs"),
                    "location_name": m.get("location_name") or m.get("filename")
                }
                break

        if not primary_geo:
            primary_geo = {
                "has_location": False,
                "lat": None,
                "lng": None,
                "height": None,
                "bounds": None,
                "crs": None
            }

        dump = trace.model_dump() if hasattr(trace, "model_dump") else trace.dict()
        final_response = {
            "request_id": trace.request_id,
            "status": "completed",
            "query": query,
            "input_mode": input_mode,
            "task": classification.task,
            "confidence": result.get("confidence", 0.90),
            "result": result,
            "inputs_metadata": loaded_metas,
            "geographic_location": primary_geo,
            "image_previews": image_previews,
            "execution_trace": dump,
            "reports": {
                "html_report_url": f"/api/v1/reports/{trace.request_id}/html",
                "json_report_url": f"/api/v1/reports/{trace.request_id}/json"
            }
        }

        MissionReportGenerator.generate_html_report(final_response, html_path)
        MissionReportGenerator.generate_json_report(final_response, json_path)

        return final_response
