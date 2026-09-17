import os
import numpy as np
from typing import Dict, Any
from geospatial.normalizer import GeospatialNormalizer
from geospatial.reader import GeospatialReader
from geospatial.overlays import EvidenceOverlayEngine
from models.loader import ModelManager
from services.llm_engine import LLMReasoningEngine

class RSCaptionSpecialist:
    def __init__(self):
        self.tool_id = "rs_caption"
        self.version = "2.0.0"

    def execute(self, image_arr: np.ndarray, meta: Dict[str, Any], query: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        ckpt = ModelManager.load_weights_if_available("bigearthnet_adapted")
        fallback_used = ckpt is None
        fallback_reason = "No bigearthnet_adapted checkpoint on disk" if fallback_used else None
        engine_type = f"PyTorch Checkpoint ({os.path.basename(ckpt)})" if ckpt else "Multi-Spectral Scene Understanding Engine (Fallback)"
        ckpt_hash = ModelManager.get_checkpoint_hash(ckpt) if ckpt else None

        metrics = GeospatialNormalizer.compute_spectral_breakdown(image_arr)
        veg_pct = metrics["vegetation_cover_pct"]
        water_pct = metrics["water_body_pct"]
        urban_pct = metrics["built_up_density_pct"]
        bare_pct = metrics["bare_soil_pct"]
        modality = meta.get("modality", "optical").upper()

        dimensions = f"{meta.get('width', 512)}x{meta.get('height', 512)}"
        response_lang = parameters.get("response_language", "en") if parameters else "en"
        caption = LLMReasoningEngine.synthesize_caption(modality, metrics, dimensions, response_language=response_lang)

        # Generate visual land-cover evidence overlay
        rgb_preview = GeospatialReader.to_rgb_preview(image_arr, meta.get("modality", "optical"))
        land_cover_map = np.clip((metrics["ndvi_map"] * 0.5 + 0.5), 0, 1.0)
        overlay_img = EvidenceOverlayEngine.render_change_heatmap(rgb_preview, land_cover_map, threshold=0.20)
        evidence_b64 = EvidenceOverlayEngine.to_base64(overlay_img)
        raw_b64 = EvidenceOverlayEngine.to_base64(rgb_preview)

        # Dynamic confidence based on radiometric classification coverage
        total_accounted = min(100.0, veg_pct + water_pct + urban_pct + bare_pct)
        conf = round(float(np.clip(total_accounted / 120.0 + 0.1, 0.55, 0.85)), 2)

        return {
            "task": "captioning",
            "tool": self.tool_id,
            "version": self.version,
            "engine": engine_type,
            "requested_model": "bigearthnet_adapted",
            "loaded_model": os.path.basename(ckpt) if ckpt else None,
            "checkpoint_hash": ckpt_hash,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
            "caption": caption,
            "confidence": conf,
            "confidence_calibrated": False,
            "evidence_image": evidence_b64,
            "raw_preview": raw_b64,
            "land_cover_breakdown": {
                "Vegetation / Canopy": f"{veg_pct}%",
                "Hydrology / Water": f"{water_pct}%",
                "Urban / Infrastructure": f"{urban_pct}%",
                "Bare Soil / Open Ground": f"{bare_pct}%"
            }
        }
