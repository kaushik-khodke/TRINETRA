"""
SatQuery AI — Master Agent Controller
The central orchestration layer. Routes requests, validates inputs, sequences specialist tools,
integrates multimodal evidence, and logs observable execution traces.
Powered by LangGraph StateGraph Workflow Runtime with PennyLane QML validation.
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
from agent.langgraph_orchestrator import LangGraphOrchestrator
from llm.agent_planner import AgentPlanner
from llm.model_registry import local_registry
from observability.langfuse_tracer import LangfuseTracer
from services.reports.report_service import MissionReportGenerator
from geospatial.reader import GeospatialReader
from geospatial.overlays import EvidenceOverlayEngine
from qml.integration.qml_service import QMLService
from qml.config import qml_config

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

class AgentController:
    def __init__(self):
        self.classifier = TaskClassifier()
        self.planner = AgentPlanner()
        self.langgraph = LangGraphOrchestrator()

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
        trace.llm_model = (active_model.active_model or active_model.default_model) if active_model else "local-llm"

        with LangfuseTracer.trace_analysis(
            query=query,
            task="pending",
            session_id=trace.request_id,
            input_mode=input_mode,
            response_language=response_language,
            metadata={"input_mode": input_mode, "num_files": len(file_paths), "model": trace.llm_model}
        ) as trace_ctx:
            trace.trace_id = trace_ctx.trace_id

            # Execute compiled LangGraph Workflow StateGraph
            final_response = self.langgraph.run(
                request_id=trace.request_id,
                trace_id=trace.trace_id,
                file_paths=file_paths,
                query=query,
                input_mode=input_mode,
                declared_modalities=declared_modalities,
                custom_parameters=custom_parameters,
                response_language=response_language
            )

            # Experimental PennyLane QML Research Validation Branch
            qml_comparison_payload = None
            try:
                task = final_response.get("detected_task", "vqa")
                if qml_config.is_task_supported(task) and qml_config.enabled and final_response.get("status") == "completed":
                    loaded_arrays = []
                    loaded_metas = []
                    for fp in file_paths:
                        try:
                            arr, meta = GeospatialReader.read_image(fp)
                            loaded_arrays.append(arr)
                            loaded_metas.append(meta.to_dict() if hasattr(meta, "to_dict") else meta)
                        except Exception:
                            pass

                    if loaded_arrays:
                        with trace_ctx.tool("qml_simulation", input_data={"device": qml_config.device_name, "qubits": qml_config.num_qubits}) as sim_span:
                            t_sim_0 = time.perf_counter()
                            qml_comparison_payload = QMLService.run_comparative_analysis(
                                task=task,
                                query=query,
                                images_arr=loaded_arrays,
                                metas=loaded_metas,
                                classical_result=final_response.get("result", final_response),
                                response_language=response_language
                            )
                            sim_latency_ms = (time.perf_counter() - t_sim_0) * 1000.0
                            if qml_comparison_payload:
                                sim_span.update(output={
                                    "device": qml_config.device_name,
                                    "qubits": qml_config.num_qubits,
                                    "layers": qml_config.num_layers,
                                    "qml_model_version": "qml_change_levir10k",
                                    "latency_ms": round(sim_latency_ms, 2)
                                })

                        if qml_comparison_payload:
                            final_response["qml_analysis"] = qml_comparison_payload.get("qml_research_branch")
                            final_response["classical_vs_qml_comparison"] = qml_comparison_payload.get("classical_vs_qml_comparison")
            except Exception as qml_err:
                print(f"[AgentController] Non-fatal QML execution notice: {qml_err}")

            # Generate mission intelligence reports if analysis was successful
            if final_response.get("status") == "completed":
                html_report_filename = f"report_{trace.request_id}.html"
                json_report_filename = f"report_{trace.request_id}.json"
                html_path = os.path.join(REPORTS_DIR, html_report_filename)
                json_path = os.path.join(REPORTS_DIR, json_report_filename)
                try:
                    MissionReportGenerator.generate_html_report(final_response, html_path)
                    MissionReportGenerator.generate_json_report(final_response, json_path)
                    final_response["reports"] = {
                        "html_report_url": f"/api/v1/reports/{trace.request_id}/html",
                        "json_report_url": f"/api/v1/reports/{trace.request_id}/json"
                    }
                except Exception as e:
                    print(f"[AgentController] Report generation note: {e}")

            trace_ctx.finalize(output={
                "status": final_response.get("status", "completed"),
                "task": final_response.get("detected_task", "unknown"),
                "confidence": final_response.get("confidence", 0.90),
                "answer": (final_response.get("answer") or "")[:250],
                "reports": final_response.get("reports")
            })

            return _make_json_safe(final_response)


def _make_json_safe(obj: Any) -> Any:
    """Recursively converts numpy scalars and non-serializable structures to standard Python JSON types."""
    import numpy as np
    if isinstance(obj, dict):
        # Exclude large raw 2D numpy arrays if any leaked into dictionaries
        return {
            k: _make_json_safe(v)
            for k, v in obj.items()
            if not (isinstance(v, np.ndarray) and v.ndim > 1)
        }
    elif isinstance(obj, list):
        return [_make_json_safe(x) for x in obj]
    elif isinstance(obj, tuple):
        return [_make_json_safe(x) for x in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj
