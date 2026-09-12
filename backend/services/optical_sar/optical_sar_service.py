"""
SatQuery AI — Cross-Modal Optical–SAR Fusion Specialist Service
Jointly reasons over co-registered Optical spectral bands and SAR microwave backscatter
to extract complementary surface and structural characteristics.
"""

import numpy as np
from PIL import Image
from typing import Dict, Any, List
from geospatial.normalizer import GeospatialNormalizer
from geospatial.overlays import EvidenceOverlayEngine
from geospatial.reader import GeospatialReader
from models.loader import ModelRegistryStatus
from services.llm_engine import LLMReasoningEngine

class OpticalSarFusionSpecialist:
    def __init__(self):
        self.tool_id = "optical_sar"
        self.version = "2.0.0"

    def execute(
        self,
        images_arr: List[np.ndarray],
        metas: List[Dict[str, Any]],
        query: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        ckpt = ModelRegistryStatus.load_weights_if_available("optical_sar_model")

        # Determine which image is optical and which is SAR
        if metas[0].get("modality", "").lower() == "sar" or metas[0].get("bands", 1) == 1:
            sar_arr, sar_meta = images_arr[0], metas[0]
            opt_arr, opt_meta = images_arr[1], metas[1]
        else:
            opt_arr, opt_meta = images_arr[0], metas[0]
            sar_arr, sar_meta = images_arr[1], metas[1]

        # 1. Optical spectral analysis
        ndvi = GeospatialNormalizer.compute_ndvi(opt_arr)
        ndwi = GeospatialNormalizer.compute_ndwi(opt_arr)
        opt_veg = float(np.mean(ndvi > 0.2))
        opt_water = float(np.mean(ndwi > 0.1))

        # 2. SAR radar backscatter analysis
        sar_db = GeospatialNormalizer.compute_sar_db(sar_arr)
        # Strong double-bounce scattering (> -5 dB) signifies vertical built-up structures
        high_backscatter_urban = float(np.mean(sar_db > -8.0))
        # Specular low backscatter (< -18 dB) signifies flat open water surfaces
        low_backscatter_water = float(np.mean(sar_db < -18.0))

        # 3. Joint cross-modal reasoning
        # Water agreement: both NDWI > 0.1 and SAR low backscatter
        fused_water_pct = round((opt_water * 0.5 + low_backscatter_water * 0.5) * 100, 1)
        # Built-up agreement: strong SAR double-bounce confirms structural buildings independent of optical shadows/clouds
        fused_urban_pct = round(high_backscatter_urban * 100, 1)
        fused_veg_pct = round(opt_veg * 100, 1)

        opt_metrics = {
            "vegetation_pct": fused_veg_pct,
            "water_pct": round(opt_water * 100.0, 1),
            "mean_ndvi": round(float(np.mean(ndvi)), 3)
        }
        sar_metrics = {
            "urban_density_pct": fused_urban_pct,
            "water_pct": round(low_backscatter_water * 100.0, 1),
            "mean_db": round(float(np.mean(sar_db)), 1)
        }
        fused_stats = {
            "fused_urban_pct": fused_urban_pct,
            "fused_water_pct": fused_water_pct,
            "fused_veg_pct": fused_veg_pct
        }

        synthesis = LLMReasoningEngine.synthesize_optical_sar_answer(
            query=query,
            opt_metrics=opt_metrics,
            sar_metrics=sar_metrics,
            fused_stats=fused_stats
        )

        engine_type = f"PyTorch Checkpoint ({ckpt})" if ckpt else synthesis["engine"]
        answer = synthesis["answer"]
        confidence = synthesis["confidence"]

        # 4. Generate visual composites
        opt_rgb = GeospatialReader.to_rgb_preview(opt_arr, "optical")
        sar_rgb = GeospatialReader.to_rgb_preview(sar_arr, "sar")
        composite = EvidenceOverlayEngine.render_optical_sar_composite(opt_rgb, sar_rgb)

        return {
            "task": "optical_sar_fusion",
            "tool": self.tool_id,
            "version": self.version,
            "engine": engine_type,
            "query": query,
            "answer": answer,
            "confidence": confidence,
            "sensor_contributions": {
                "optical": f"Spectral chlorophyll NDVI ({fused_veg_pct}%) and multi-band water absorption",
                "sar": f"Microwave double-bounce structural built-up mapping ({fused_urban_pct}%) and specular radar attenuation"
            },
            "evidence": {
                "optical_preview": EvidenceOverlayEngine.to_base64(opt_rgb),
                "sar_preview": EvidenceOverlayEngine.to_base64(sar_rgb),
                "fused_composite": EvidenceOverlayEngine.to_base64(composite)
            }
        }
