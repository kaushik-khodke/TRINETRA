"""
SatQuery AI — Specialist Tool Registry
Defines all specialist tools, capabilities, permitted parameters,
supported modalities, and metadata for the agentic orchestrator.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field

class SpecialistTool(BaseModel):
    tool_id: str
    name: str
    version: str
    description: str
    supported_tasks: List[str]
    supported_modalities: List[str]
    min_inputs: int = 1
    max_inputs: int = 1
    requires_geospatial: bool = False
    permitted_parameters: Dict[str, Any] = Field(default_factory=dict)
    output_types: List[str] = Field(default_factory=lambda: ["text", "confidence", "evidence"])

TOOL_REGISTRY: Dict[str, SpecialistTool] = {
    "validator": SpecialistTool(
        tool_id="validator",
        name="Input & Pair Compatibility Validator",
        version="1.2.0",
        description="Inspects file format, raster readability, spatial bounds, CRS, band count, modality, and pair compatibility before inference.",
        supported_tasks=["validation"],
        supported_modalities=["optical", "multispectral", "sar"],
        min_inputs=1,
        max_inputs=2,
        requires_geospatial=True,
        permitted_parameters={
            "strict_crs_check": True,
            "allow_benchmark_png": True
        },
        output_types=["validation_report", "metadata"]
    ),
    "rs_vqa": SpecialistTool(
        tool_id="rs_vqa",
        name="Remote-Sensing VQA Specialist",
        version="2.0.0",
        description="Answers complex domain-specific questions on single optical, multispectral, or SAR remote-sensing imagery.",
        supported_tasks=["vqa"],
        supported_modalities=["optical", "multispectral", "sar"],
        min_inputs=1,
        max_inputs=1,
        requires_geospatial=False,
        permitted_parameters={
            "confidence_threshold": 0.65,
            "max_tokens": 128,
            "temperature": 0.2
        },
        output_types=["text", "confidence", "evidence"]
    ),
    "rs_caption": SpecialistTool(
        tool_id="rs_caption",
        name="Remote-Sensing Scene Captioning Specialist",
        version="1.8.0",
        description="Generates rich, structured scene descriptions and land-cover summaries for single satellite images.",
        supported_tasks=["captioning", "scene_description"],
        supported_modalities=["optical", "multispectral", "sar"],
        min_inputs=1,
        max_inputs=1,
        requires_geospatial=False,
        permitted_parameters={
            "detail_level": "comprehensive",
            "extract_landcover_stats": True
        },
        output_types=["text", "confidence", "evidence"]
    ),
    "rs_ground": SpecialistTool(
        tool_id="rs_ground",
        name="Text-Guided Region Grounding Specialist",
        version="1.5.0",
        description="Locates, segments, and highlights specific geospatial objects and land features referenced in natural-language queries.",
        supported_tasks=["grounding", "localization"],
        supported_modalities=["optical", "multispectral", "sar"],
        min_inputs=1,
        max_inputs=1,
        requires_geospatial=True,
        permitted_parameters={
            "iou_threshold": 0.5,
            "box_format": "normalized_xyxy",
            "generate_polygon_mask": True
        },
        output_types=["boxes", "masks", "confidence", "evidence"]
    ),
    "change_ai": SpecialistTool(
        tool_id="change_ai",
        name="Bi-Temporal Change Understanding Specialist",
        version="2.1.0",
        description="Analyzes spatially corresponding image pairs acquired at different timestamps to identify, describe, and locate temporal land shifts.",
        supported_tasks=["change_detection", "change_description", "change_vqa"],
        supported_modalities=["optical", "multispectral", "sar"],
        min_inputs=2,
        max_inputs=2,
        requires_geospatial=True,
        permitted_parameters={
            "difference_method": "differential_feature_fusion",
            "sensitivity_threshold": 0.35,
            "generate_change_map": True
        },
        output_types=["change_description", "change_map", "confidence", "evidence"]
    ),
    "optical_sar": SpecialistTool(
        tool_id="optical_sar",
        name="Cross-Modal Optical–SAR Fusion Specialist",
        version="2.0.0",
        description="Extracts complementary spectral (optical) and structural/backscatter (SAR) information from co-registered multimodal image pairs.",
        supported_tasks=["optical_sar_fusion", "multimodal_joint_analysis"],
        supported_modalities=["optical", "sar"],
        min_inputs=2,
        max_inputs=2,
        requires_geospatial=True,
        permitted_parameters={
            "fusion_stage": "cross_attention_feature_fusion",
            "sar_polarization": "VV_VH",
            "extract_builtup_water": True
        },
        output_types=["text", "confidence", "fusion_map", "evidence"]
    ),
    "report_gen": SpecialistTool(
        tool_id="report_gen",
        name="Mission Intelligence Report Generator",
        version="1.0.0",
        description="Compiles analysis results, evidence imagery, confidence metrics, and execution traces into downloadable PDF and JSON reports.",
        supported_tasks=["reporting"],
        supported_modalities=["optical", "multispectral", "sar"],
        min_inputs=1,
        max_inputs=2,
        permitted_parameters={
            "format": "pdf",
            "include_execution_trace": True,
            "include_spectral_metadata": True
        },
        output_types=["report_file"]
    )
}

def get_tool(tool_id: str) -> SpecialistTool:
    if tool_id not in TOOL_REGISTRY:
        raise ValueError(f"Specialist tool '{tool_id}' not found in registry.")
    return TOOL_REGISTRY[tool_id]

def list_tools() -> List[Dict[str, Any]]:
    return [tool.dict() for tool in TOOL_REGISTRY.values()]
