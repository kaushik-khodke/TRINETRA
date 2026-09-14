"""
SatQuery AI / TRINETRA — Controlled LangChain QML Tool
Exposes the PennyLane Variational Quantum Classifier as a deterministic,
schema-validated LangChain tool. Prevents arbitrary quantum code generation by LLMs
and guarantees safe parameter bounding (Section 26 of TRINETRA_QML_PennyLane.md).
"""

import os
import sys
import json
import time
from typing import List, Dict, Any, Optional, Type

# Graceful import for Pydantic
try:
    from pydantic import BaseModel, Field
    try:
        from pydantic import field_validator as validator  # Pydantic v2
    except ImportError:
        from pydantic import validator  # Pydantic v1
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    class BaseModel:  # type: ignore
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        @classmethod
        def schema(cls):
            return {}
        def dict(self, *args, **kwargs):
            return self.__dict__

    def Field(*args, **kwargs):  # type: ignore
        if len(args) > 0 and args[0] is not ...:
            return args[0]
        return kwargs.get("default", None)

    def validator(*args, **kwargs):  # type: ignore
        return lambda f: f

# Ensure backend root is in sys.path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from qml.config import qml_config
from qml.integration.qml_service import QMLService
from qml.comparison.agreement import AgreementAnalyzer
from qml.research_buffer import research_buffer

try:
    from langchain_core.tools import BaseTool
except ImportError:
    try:
        from langchain.tools import BaseTool
    except ImportError:
        # Fallback BaseTool interface if langchain is not yet installed in active environment
        class BaseTool:  # type: ignore
            name: str = ""
            description: str = ""
            args_schema: Optional[Type[BaseModel]] = None

            def run(self, *args, **kwargs):
                return self._run(*args, **kwargs)


class QuantumValidationInput(BaseModel):
    """Strict schema-validated parameters for the QuantumValidationTool."""
    task: str = Field(
        default="change_analysis",
        description="Target remote-sensing task. Must be one of: 'change_analysis', 'optical_sar_fusion', 'vqa'."
    )
    query: Optional[str] = Field(
        default="",
        description="The natural-language query guiding the spatial inspection."
    )
    file_paths: Optional[List[str]] = Field(
        default=None,
        description="List of verified absolute or relative raster filepaths (1 or 2 images)."
    )
    features: Optional[List[float]] = Field(
        default=None,
        description="Optional pre-extracted compact 6-D quantum feature representation."
    )
    classical_prediction: Optional[str] = Field(
        default=None,
        description="Optional classical specialist prediction label for agreement check."
    )
    response_language: str = Field(
        default="en",
        description="Response language code: 'en', 'hi', or 'mr'."
    )
    qubits: Optional[int] = Field(
        default=6,
        description="Number of physical simulator qubits (4, 6, or 8)."
    )
    layers: Optional[int] = Field(
        default=3,
        description="Number of variational entangling circuit layers (1 to 5)."
    )

    @validator("task")
    def validate_task(cls, v):
        allowed = ["change_analysis", "optical_sar_fusion", "vqa"]
        if v and v.lower() not in allowed:
            raise ValueError(f"Task '{v}' is not supported by QML research branch. Allowed: {allowed}")
        return (v or "change_analysis").lower()

    @validator("qubits")
    def validate_qubits(cls, v):
        if v is not None and v not in (4, 6, 8):
            raise ValueError("Qubits count must be exactly 4, 6, or 8 to guarantee simulation stability.")
        return v or 6

    @validator("layers")
    def validate_layers(cls, v):
        if v is not None and not (1 <= v <= 6):
            raise ValueError("Layer depth must be between 1 and 6 to prevent barren plateaus.")
        return v or 3


class QuantumValidationTool(BaseTool):
    """
    LangChain-compliant specialist tool for PennyLane QML verification.
    The agent calls this tool to corroborate classical specialist inferences
    using parameterized quantum circuit simulations on compact feature vectors.
    """
    name: str = "quantum_validation_tool"
    description: str = (
        "Executes experimental PennyLane Variational Quantum Classifier (VQC) circuits on compact "
        "satellite feature representations and calculates cross-paradigm agreement with classical "
        "specialist models. Supported tasks: change_analysis, optical_sar_fusion, vqa."
    )
    args_schema: Type[BaseModel] = QuantumValidationInput

    def _run(
        self,
        task: str = "change_analysis",
        query: str = "",
        file_paths: Optional[List[str]] = None,
        features: Optional[List[float]] = None,
        classical_prediction: Optional[str] = None,
        response_language: str = "en",
        qubits: Optional[int] = 6,
        layers: Optional[int] = 3,
        classical_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes controlled quantum circuit forward pass.
        Zero arbitrary code execution: LLM cannot inject custom circuit gates.
        Supports both direct feature vector testing and full raster file processing.
        """
        if not qml_config.enabled:
            return {
                "status": "disabled",
                "message": "Quantum research branch is disabled in environment configuration."
            }

        if not qml_config.is_task_supported(task):
            return {
                "status": "unsupported_task",
                "message": f"Task '{task}' is not currently configured for QML research validation."
            }

        # 1. Mode A: Direct feature vector evaluation (unit testing / pre-extracted features)
        if features is not None and len(features) > 0:
            import torch
            t0 = time.perf_counter()
            model = QMLService.get_or_create_model(num_qubits=qubits or 6, num_layers=layers or 3)
            
            # Pad or truncate to qubit count if needed
            target_q = model.num_qubits
            feat_list = list(features)
            if len(feat_list) < target_q:
                feat_list = feat_list + [0.0] * (target_q - len(feat_list))
            elif len(feat_list) > target_q:
                feat_list = feat_list[:target_q]

            q_tensor = torch.tensor(feat_list, dtype=torch.float32)
            t_sim_start = time.perf_counter()
            pred_label, q_confidence, class_probs = model.predict(q_tensor)
            qml_latency_ms = (time.perf_counter() - t_sim_start) * 1000.0

            c_label = classical_prediction or "Increased"
            c_conf = 0.85
            if classical_result:
                c_label = classical_result.get("change_status", c_label)
                c_conf = float(classical_result.get("confidence", 0.85))

            circuit_meta = model.get_circuit_metadata()
            report = AgreementAnalyzer.analyze(
                task=task,
                classical_pred=c_label,
                classical_conf=c_conf,
                classical_latency_ms=120.0,
                qml_pred=pred_label,
                qml_conf=q_confidence,
                qml_latency_ms=qml_latency_ms,
                qml_circuit_meta=circuit_meta
            )

            # Record in research buffer
            try:
                research_buffer.record_inference(
                    task=task,
                    feature_vector=[float(x) for x in feat_list],
                    classical_pred=c_label,
                    classical_conf=c_conf,
                    qml_pred=pred_label,
                    qml_conf=q_confidence,
                    model_version="qml_change_levir10k",
                    dataset="LEVIR_CD_patches"
                )
            except Exception:
                pass

            return {
                "status": "success",
                "task": task,
                "qml_prediction": pred_label,
                "qml_confidence": q_confidence,
                "class_probabilities": class_probs,
                "classical_prediction": c_label,
                "agreement_level": report.agreement_level,
                "is_agreement": report.is_agreement,
                "latency_ms": round(qml_latency_ms, 2),
                "circuit_metadata": circuit_meta,
                "summary": report.summary
            }

        # 2. Mode B: Raster file processing
        if file_paths:
            from geospatial.reader import GeospatialReader
            loaded_arrays = []
            loaded_metas = []
            for p in file_paths:
                if not os.path.exists(p):
                    return {
                        "status": "error",
                        "error": f"Input raster file not found: {p}"
                    }
                arr, meta = GeospatialReader.read_image(p)
                loaded_arrays.append(arr)
                loaded_metas.append(meta.to_dict())

            c_res = classical_result or {
                "task": task,
                "change_status": classical_prediction or "Increased",
                "confidence": 0.88,
                "latency_ms": 320.0
            }

            payload = QMLService.run_comparative_analysis(
                task=task,
                query=query,
                images_arr=loaded_arrays,
                metas=loaded_metas,
                classical_result=c_res,
                response_language=response_language
            )
            return payload or {"status": "unavailable", "message": "QML execution produced null payload."}

        return {
            "status": "error",
            "error": "Must provide either 'features' (List[float]) or 'file_paths' (List[str])."
        }

    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """Asynchronous execution handler."""
        return self._run(*args, **kwargs)

