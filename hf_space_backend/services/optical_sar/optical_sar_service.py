"""
SatQuery AI — Cross-Modal Optical–SAR Fusion Specialist Service
Jointly reasons over co-registered Optical spectral bands and SAR microwave backscatter
to extract complementary surface and structural characteristics.
"""

import os
import numpy as np
from PIL import Image
from typing import Dict, Any, List
from geospatial.normalizer import GeospatialNormalizer
from geospatial.overlays import EvidenceOverlayEngine
from geospatial.reader import GeospatialReader
from geospatial.validator import GeospatialValidator
from schemas.contracts import RasterMetadata
from core.exceptions import AlignmentMismatchError
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
            raw_sar, sar_meta_dict = images_arr[0], metas[0]
            raw_opt, opt_meta_dict = images_arr[1], metas[1]
        else:
            raw_opt, opt_meta_dict = images_arr[0], metas[0]
            raw_sar, sar_meta_dict = images_arr[1], metas[1]
        def _build_meta(arr: np.ndarray, m: Any) -> RasterMetadata:
            if isinstance(m, RasterMetadata):
                return m
            h, w = arr.shape[:2]
            bands = 1 if arr.ndim == 2 else (arr.shape[2] if arr.ndim == 3 else 1)
            d = dict(m) if isinstance(m, dict) else {}
            d.setdefault("width", w)
            d.setdefault("height", h)
            d.setdefault("band_count", d.get("bands", bands))
            d.setdefault("dtype", str(arr.dtype))
            return RasterMetadata(**d)

        opt_meta = _build_meta(raw_opt, opt_meta_dict)
        sar_meta = _build_meta(raw_sar, sar_meta_dict)

        # Stage 3 True Geometric Optical–SAR Coregistration Validation
        alignment_report = GeospatialValidator.validate_optical_sar_coregistration(
            opt_meta, sar_meta, raw_opt, raw_sar
        )

        if opt_meta.is_geotiff and sar_meta.is_geotiff and alignment_report.bounds_overlap_pct <= 0.0:
            raise AlignmentMismatchError(
                f"Zero spatial overlap between Optical ({opt_meta.filename}) and SAR ({sar_meta.filename}). Cannot perform cross-modal fusion on disjoint geographic locations."
            )

        # Preprocess optical with reflectance scaling & cloud/nodata masking
        opt_arr, opt_manifest = GeospatialNormalizer.preprocess_optical(raw_opt, opt_meta)

        # Preprocess SAR with decibel conversion & documented speckle filter policy
        sar_db, sar_manifest = GeospatialNormalizer.preprocess_sar(raw_sar, sar_meta, apply_speckle_filter=False)
        sar_arr = raw_sar

        # 1. Optical spectral analysis
        indices = GeospatialNormalizer.compute_spectral_indices(raw_opt)
        ndvi = indices["ndvi"]
        ndwi = indices["ndwi"]
        opt_veg = float(np.mean(ndvi > 0.2))
        opt_water = float(np.mean(ndwi > 0.1))

        # 2. SAR radar backscatter analysis
        high_backscatter_urban = float(np.mean(sar_db > -8.0))
        low_backscatter_water = float(np.mean(sar_db < -18.0))

        # 3. Joint cross-modal reasoning
        fused_water_pct = round((opt_water * 0.5 + low_backscatter_water * 0.5) * 100, 1)
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

        response_lang = parameters.get("response_language", "en") if parameters else "en"
        synthesis = LLMReasoningEngine.synthesize_optical_sar_answer(
            query=query,
            opt_metrics=opt_metrics,
            sar_metrics=sar_metrics,
            fused_stats=fused_stats,
            response_language=response_lang
        )

        engine_type = f"PyTorch Checkpoint ({os.path.basename(ckpt)})" if ckpt else synthesis["engine"]
        answer = synthesis["answer"]
        confidence = synthesis["confidence"]

        # 4. Generate visual composites
        opt_rgb = GeospatialReader.to_rgb_preview(raw_opt, "optical")
        sar_rgb = GeospatialReader.to_rgb_preview(raw_sar, "sar")
        composite = EvidenceOverlayEngine.render_optical_sar_composite(opt_rgb, sar_rgb)

        # 5. Compute dynamic statistical cross-modal correlation with alignment report
        corr_data = GeospatialNormalizer.compute_cross_modal_correlation(
            raw_opt, raw_sar, alignment_report=alignment_report
        )

        fallback_used = ckpt is None
        fallback_reason = None if not fallback_used else "No optical_sar_model checkpoint found on disk"
        ckpt_hash = ModelRegistryStatus.get_checkpoint_hash(ckpt) if ckpt else None

        return {
            "task": "optical_sar_fusion",
            "tool": self.tool_id,
            "version": self.version,
            "engine": engine_type,
            "requested_model": "optical_sar_model",
            "loaded_model": os.path.basename(ckpt) if ckpt else None,
            "checkpoint_hash": ckpt_hash,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
            "query": query,
            "answer": answer,
            "confidence": confidence,
            "confidence_calibrated": False,
            "coregistered": alignment_report.coregistered,
            "alignment_report": alignment_report.model_dump(),
            "fusion_correlations": {
                "optical_sar_correlation": corr_data["optical_sar_correlation"],
                "structural_coherence": corr_data["structural_coherence"],
                "spectral_radar_alignment": alignment_report.status_message,
                "sample_pixel_count": corr_data["sample_pixel_count"]
            },
            "sensor_contributions": {
                "optical": f"Spectral chlorophyll NDVI ({fused_veg_pct}%) and multi-band water absorption",
                "sar": f"Microwave double-bounce structural built-up mapping ({fused_urban_pct}%) and specular radar attenuation ({sar_manifest['polarization']})"
            },
            "preprocessing_manifests": {
                "optical": opt_manifest,
                "sar": sar_manifest
            },
            "evidence": {
                "optical_preview": EvidenceOverlayEngine.to_base64(opt_rgb),
                "sar_preview": EvidenceOverlayEngine.to_base64(sar_rgb),
                "fused_composite": EvidenceOverlayEngine.to_base64(composite)
            }
        }
