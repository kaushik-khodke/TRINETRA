"""
SatQuery AI — Bi-Temporal Change Specialist Service
Performs differential change analysis, answers change-based questions,
quantifies urban/land shifts, and generates visual change maps.
"""

import numpy as np
from PIL import Image
from typing import Dict, Any, List
from geospatial.normalizer import GeospatialNormalizer
from geospatial.overlays import EvidenceOverlayEngine
from geospatial.reader import GeospatialReader
from models.loader import ModelRegistryStatus
from services.llm_engine import LLMReasoningEngine

class BiTemporalChangeSpecialist:
    def __init__(self):
        self.tool_id = "change_ai"
        self.version = "2.1.0"

    def execute(
        self,
        images_arr: List[np.ndarray],
        metas: List[Dict[str, Any]],
        query: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        ckpt = ModelRegistryStatus.load_weights_if_available("change_specialist_model")

        arr_t1 = images_arr[0]
        arr_t2 = images_arr[1]

        # Compute difference matrix & statistics
        diff_matrix, stats = GeospatialNormalizer.compute_bitemporal_change(arr_t1, arr_t2)

        # Synthesize evidence-grounded answer via LLM reasoning engine
        spatial_dist = {
            "quadrants": stats.get("quadrants", {}),
            "top_sectors": stats.get("top_sectors", []),
            "trend": stats.get("trend", "expansion")
        }

        response_lang = parameters.get("response_language", "en") if parameters else "en"
        synthesis = LLMReasoningEngine.synthesize_change_answer(
            query=query,
            change_stats=stats,
            spatial_distribution=spatial_dist,
            response_language=response_lang
        )

        engine_type = f"PyTorch Checkpoint ({ckpt})" if ckpt else synthesis["engine"]
        answer = synthesis["answer"]
        confidence = synthesis["confidence"]
        status = stats.get("trend", "detected")

        # Render visual change heatmap overlay on T2
        rgb_t1 = GeospatialReader.to_rgb_preview(arr_t1, metas[0].get("modality", "optical"))
        rgb_t2 = GeospatialReader.to_rgb_preview(arr_t2, metas[1].get("modality", "optical"))
        
        change_map_img = EvidenceOverlayEngine.render_change_heatmap(rgb_t2, diff_matrix, threshold=0.25)
        
        preview_t1_b64 = EvidenceOverlayEngine.to_base64(rgb_t1)
        preview_t2_b64 = EvidenceOverlayEngine.to_base64(rgb_t2)
        change_map_b64 = EvidenceOverlayEngine.to_base64(change_map_img)

        return {
            "task": "change_analysis",
            "tool": self.tool_id,
            "version": self.version,
            "engine": engine_type,
            "query": query,
            "answer": answer,
            "change_status": status,
            "confidence": round(confidence, 2),
            "change_statistics": stats,
            "evidence": {
                "t1_preview": preview_t1_b64,
                "t2_preview": preview_t2_b64,
                "change_heatmap": change_map_b64
            }
        }
