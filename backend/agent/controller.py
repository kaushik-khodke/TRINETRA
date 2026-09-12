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
from llm.agent_planner import AgentPlanner
from llm.model_registry import local_registry
from observability.langfuse_tracer import LangfuseTracer
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
        self.planner = AgentPlanner()
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
        custom_parameters: Optional[Dict[str, Any]] = None,
        response_language: str = "en"
    ) -> Dict[str, Any]:
        trace = ExecutionTrace(
            input_mode=input_mode,
            query=query,
            detected_task="pending"
        )
        active_model = local_registry.get_active_model()
        trace.llm_model = (active_model.active_model or active_model.default_model) if active_model else "qwen3.5:9b"

        with LangfuseTracer.trace_analysis(
            query=query,
            task="pending",
            session_id=trace.request_id,
            metadata={"input_mode": input_mode, "num_files": len(file_paths), "model": trace.llm_model}
        ) as trace_ctx:
            trace.trace_id = trace_ctx.trace_id

            # Step 1: Input Validation
            with trace_ctx.span("input_validation", input_data={"files": file_paths, "mode": input_mode}) as span:
                trace.add_step(
                    stage="validation",
                    action="inspect_inputs",
                    tool="validator",
                    details=f"Validating {len(file_paths)} input raster(s) for mode '{input_mode}'."
                )

                # Security check: file paths must exist and be accessible
                for p in file_paths:
                    if not os.path.isfile(p):
                        err = f"Target raster file does not exist: {p}"
                        span.update(output={"error": err})
                        trace.fail(err)
                        dump = trace.model_dump() if hasattr(trace, "model_dump") else trace.dict()
                        return {
                            "request_id": trace.request_id,
                            "trace_id": trace.trace_id,
                            "status": "failed",
                            "error": err,
                            "execution_trace": dump
                        }

                val_report = InputValidator.validate(file_paths, requested_mode=input_mode, declared_modalities=declared_modalities)
                if not val_report.valid:
                    err = val_report.error_message or "Input validation failed."
                    span.update(output={"error": err})
                    trace.fail(err)
                    dump = trace.model_dump() if hasattr(trace, "model_dump") else trace.dict()
                    return {
                        "request_id": trace.request_id,
                        "trace_id": trace.trace_id,
                        "status": "failed",
                        "error": err,
                        "execution_trace": dump
                    }

                span.update(output={"status": "valid", "file_count": len(file_paths)})
                trace.add_step(
                    stage="validation",
                    action="validation_passed",
                    tool="validator",
                    details=f"All files verified: {', '.join(os.path.basename(p) for p in file_paths)}."
                )

            # Step 2: Agent Planning & Task Classification
            num_images = len(file_paths)
            image_modalities = [m["modality"] for m in val_report.images_metadata]

            with trace_ctx.span("agent_planning", input_data={"query": query, "modalities": image_modalities}) as span:
                exec_plan = self.planner.plan(
                    query=query,
                    input_mode=input_mode,
                    num_images=num_images,
                    image_modalities=image_modalities
                )
                classification = self.classifier.classify(query, input_mode, num_images, image_modalities)
                
                # Align detected task
                task = exec_plan.intent.task if exec_plan.intent.task else classification.task
                trace.detected_task = task

                span.update(output={
                    "task": task,
                    "confidence": exec_plan.intent.confidence,
                    "target_features": exec_plan.intent.target_features,
                    "reasoning": exec_plan.intent.reasoning
                })

                trace.add_step(
                    stage="planning",
                    action="decompose_query",
                    details=f"Multi-step agent plan formed for task '{task}' with confidence {exec_plan.intent.confidence:.2f}. Strategy: {exec_plan.intent.reasoning}"
                )

            # Step 3: Specialist Tool Selection & Strict Parameter Safety
            target_tool_id = classification.recommended_tools[1] if len(classification.recommended_tools) > 1 else "rs_vqa"
            tool_meta = get_tool(target_tool_id)

            with trace_ctx.span("tool_parameter_safety", input_data={"tool": tool_meta.tool_id, "custom_params": custom_parameters}) as span:
                permitted_params = tool_meta.permitted_parameters.copy()
                if custom_parameters:
                    for k, v in custom_parameters.items():
                        if k in permitted_params:
                            # Bound check thresholds
                            if "threshold" in k and isinstance(v, (int, float)):
                                if 0.0 <= float(v) <= 1.0:
                                    permitted_params[k] = float(v)
                            elif "sar_threshold_db" in k and isinstance(v, (int, float)):
                                if -50.0 <= float(v) <= 50.0:
                                    permitted_params[k] = float(v)
                            elif isinstance(v, (str, int, float, bool, list)):
                                permitted_params[k] = v

                permitted_params["response_language"] = response_language

                trace.selected_tools = [
                    {"name": "validator", "version": "1.2.0"},
                    {"name": tool_meta.name, "version": tool_meta.version}
                ]
                trace.parameters = permitted_params
                span.update(output={"selected_tool": tool_meta.name, "safe_parameters": permitted_params})

                trace.add_step(
                    stage="planning",
                    action="select_specialist_tool",
                    tool=tool_meta.tool_id,
                    parameters=permitted_params,
                    details=f"Selected tool '{tool_meta.name}' [{tool_meta.version}] with verified safe parameters."
                )

            # Step 4: Raster Ingestion
            with trace_ctx.span("raster_ingestion", input_data={"files": file_paths}) as span:
                loaded_arrays = []
                loaded_metas = []
                image_previews = []
                for i, path in enumerate(file_paths):
                    arr, meta = GeospatialReader.read_image(path, detected_modality=image_modalities[i])
                    loaded_arrays.append(arr)
                    loaded_metas.append(meta.to_dict())
                    rgb_preview = GeospatialReader.to_rgb_preview(arr, image_modalities[i])
                    image_previews.append(EvidenceOverlayEngine.to_base64(rgb_preview))

                span.update(output={"loaded_count": len(loaded_arrays), "dimensions": [m.get("shape") for m in loaded_metas]})

            # Step 5: Execute Specialist Workflow
            trace.add_step(
                stage="execution",
                action="run_inference",
                tool=tool_meta.tool_id,
                details=f"Invoking {tool_meta.name} with inputs."
            )

            try:
                with trace_ctx.span("specialist_execution", input_data={"task": task, "tool": tool_meta.tool_id}) as span:
                    if task == "optical_sar_fusion":
                        result = self.optical_sar_specialist.execute(
                            images_arr=loaded_arrays,
                            metas=loaded_metas,
                            query=query,
                            parameters=permitted_params
                        )
                    elif task == "change_analysis":
                        result = self.change_specialist.execute(
                            images_arr=loaded_arrays,
                            metas=loaded_metas,
                            query=query,
                            parameters=permitted_params
                        )
                    elif task == "grounding":
                        result = self.grounding_specialist.execute(
                            image_arr=loaded_arrays[0],
                            meta=loaded_metas[0],
                            query=query,
                            parameters=permitted_params
                        )
                    elif task == "captioning":
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

                    span.update(output={
                        "confidence": result.get("confidence", 0.90),
                        "answer_snippet": (result.get("answer") or result.get("caption") or "")[:120]
                    })

                trace.add_step(
                    stage="integration",
                    action="integrate_evidence",
                    tool=tool_meta.tool_id,
                    details="Integrated textual conclusions, visual evidence overlays, and confidence metrics."
                )

            except Exception as e:
                trace_ctx.record_error(str(e))
                trace.fail(f"Specialist tool execution error: {str(e)}")
                dump = trace.model_dump() if hasattr(trace, "model_dump") else trace.dict()
                return {
                    "request_id": trace.request_id,
                    "trace_id": trace.trace_id,
                    "status": "failed",
                    "error": str(e),
                    "execution_trace": dump
                }

            # Step 6: Generate Downloadable Report Files
            report_html_filename = f"report_{trace.request_id[:8]}.html"
            report_json_filename = f"report_{trace.request_id[:8]}.json"
            html_path = os.path.join(REPORTS_DIR, report_html_filename)
            json_path = os.path.join(REPORTS_DIR, report_json_filename)

            trace.complete(status="completed")

            dump = trace.model_dump() if hasattr(trace, "model_dump") else trace.dict()
            final_response = {
                "request_id": trace.request_id,
                "trace_id": trace.trace_id,
                "status": "completed",
                "query": query,
                "input_mode": input_mode,
                "response_language": response_language,
                "task": task,
                "agent_framework": "langchain",
                "llm_model": trace.llm_model,
                "cloud_llm": False,
                "confidence": result.get("confidence", 0.90),
                "result": result,
                "inputs_metadata": loaded_metas,
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
