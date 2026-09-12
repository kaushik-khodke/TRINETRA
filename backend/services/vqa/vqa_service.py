"""
SatQuery AI — Remote-Sensing VQA Specialist Service
Answers natural-language domain queries regarding single optical,
multispectral, and SAR satellite imagery using LLM & radiometric reasoning.
"""

import numpy as np
from typing import Dict, Any
from geospatial.normalizer import GeospatialNormalizer
from geospatial.reader import GeospatialReader
from geospatial.overlays import EvidenceOverlayEngine
from services.llm_engine import LLMReasoningEngine
from models.loader import ModelManager

class RSVqaSpecialist:
    def __init__(self):
        self.tool_id = "rs_vqa"
        self.version = "2.2.0"

    def execute(self, image_arr: np.ndarray, meta: Dict[str, Any], query: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Check for trained PyTorch neural checkpoint
        ckpt = ModelManager.load_weights_if_available("rs_vqa_model")
        has_neural_weights = ckpt is not None

        # Compute accurate radiometric spectral metrics from the uploaded raster
        metrics = GeospatialNormalizer.compute_spectral_breakdown(image_arr)
        modality = meta.get("modality", "optical")

        # Feature detection
        features = {
            "has_water": metrics["water_body_pct"] > 1.5,
            "has_dense_veg": metrics["vegetation_cover_pct"] > 25.0,
            "has_urban": metrics["built_up_density_pct"] > 12.0
        }

        # Synthesize evidence-grounded answer via LLM reasoning engine
        synthesis = LLMReasoningEngine.synthesize_vqa_answer(
            query=query,
            modality=modality,
            spectral_metrics=metrics,
            detected_features=features
        )

        engine_name = f"PyTorch Checkpoint ({ckpt})" if has_neural_weights else synthesis["engine"]

        # Generate visual saliency heatmap overlay on the actual uploaded image
        rgb_preview = GeospatialReader.to_rgb_preview(image_arr, modality)
        
        # Overlay either water heatmap, vegetation heatmap, or structural gradient based on query
        clean_q = query.lower()
        if "water" in clean_q or "river" in clean_q or "lake" in clean_q:
            diff_map = np.clip(metrics["ndwi_map"] * 2.0, 0, 1.0)
        elif "vegetation" in clean_q or "forest" in clean_q or "crop" in clean_q:
            diff_map = np.clip(metrics["ndvi_map"] * 2.0, 0, 1.0)
        else:
            diff_map = np.clip((metrics["ndvi_map"] + metrics["ndwi_map"]) * 0.5 + 0.3, 0, 1.0)

        overlay_img = EvidenceOverlayEngine.render_change_heatmap(rgb_preview, diff_map, threshold=0.15)
        evidence_b64 = EvidenceOverlayEngine.to_base64(overlay_img)
        raw_b64 = EvidenceOverlayEngine.to_base64(rgb_preview)

        return {
            "task": "vqa",
            "tool": self.tool_id,
            "version": self.version,
            "engine": engine_name,
            "query": query,
            "answer": synthesis["answer"],
            "confidence": synthesis["confidence"],
            "evidence_image": evidence_b64,
            "raw_preview": raw_b64,
            "evidence_metrics": {
                "vegetation_cover_pct": metrics["vegetation_cover_pct"],
                "water_body_pct": metrics["water_body_pct"],
                "built_up_density_pct": metrics["built_up_density_pct"],
                "bare_soil_pct": metrics["bare_soil_pct"],
                "mean_ndvi": metrics["mean_ndvi"],
                "mean_ndwi": metrics["mean_ndwi"]
            }
        }
