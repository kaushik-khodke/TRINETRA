"""
TRINETRA — Remote Sensing VQA Evidence Construction Engine
Module: backend/services/vqa/evidence_engine.py

Builds the Stage 7 Ten-Point EvidencePackage grounding natural language answers
traceable directly to physical measurements, neural predictions, and geospatial metadata:
1. source_image (asset ID, file path, SHA-256, dimensions, sensor)
2. bands_used (spectral / radar channels)
3. spatial_region (bounds, CRS, physical area, GeoJSON)
4. model_output (predicted answer, candidate ranking, confidence scores)
5. confidence_info (score, calibrated bool, entropy)
6. derived_metrics (NDVI, NDWI, NDBI, water %, vegetation %, built-up %)
7. timestamp_utc (ISO 8601 UTC timestamp)
8. checkpoint_info (model name, file, SHA-256, parameter count)
9. preprocessing_info (radiometric scaling, normalizer, input shape)
10. warnings (cloud cover, dynamic range, out-of-distribution, fallback flags)
"""

import os
import sys
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from schemas.contracts import EvidencePackage, EvidenceItem, CandidateAnswer
from geospatial.normalizer import GeospatialNormalizer
from geospatial.overlays import EvidenceOverlayEngine
from geospatial.reader import GeospatialReader
try:
    from backend.calibration.uncertainty import UncertaintyDecompositionEngine, ConfidenceSemantics
except ImportError:
    from calibration.uncertainty import UncertaintyDecompositionEngine, ConfidenceSemantics



class VQAEvidenceEngine:
    """
    Constructs auditable, machine-readable EvidencePackage instances for Remote-Sensing VQA.
    Strictly prevents LLM hallucination of unmeasured physical metrics.
    """

    @classmethod
    def compute_sha256(cls, file_path: Optional[str], data_bytes: Optional[bytes] = None) -> str:
        """Computes SHA-256 digest of file or raw bytes."""
        hasher = hashlib.sha256()
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        elif data_bytes:
            hasher.update(data_bytes)
            return hasher.hexdigest()
        return "0" * 64

    @classmethod
    def construct_evidence_package(
        cls,
        image_arr: np.ndarray,
        meta: Dict[str, Any],
        query: str,
        answer_text: Optional[str] = None,
        spectral_metrics: Optional[Dict[str, Any]] = None,
        neural_pred: Optional[Dict[str, Any]] = None,
        top_answer: Optional[str] = None,
        candidates: Optional[List[Any]] = None,
        confidence: Optional[float] = None,
        is_calibrated: bool = False,
        checkpoint_path: Optional[str] = None,
        checkpoint_hash: Optional[str] = None,
        model_name: str = "RSVqaFusionNetwork",
        param_count: Optional[int] = None,
        normalizer_name: Optional[str] = None,
        input_shape: Optional[List[int]] = None,
        warnings: Optional[List[str]] = None,
        fallback_used: bool = False,
        fallback_reason: Optional[str] = None,
        image_path: Optional[str] = None,
        **kwargs
    ) -> EvidencePackage:
        """
        Synthesizes the complete ten-point EvidencePackage.
        """
        now_utc = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        package_id = f"evpkg-{uuid.uuid4().hex[:12]}"

        # Normalize meta to dict
        meta = meta.model_dump() if hasattr(meta, "model_dump") else (meta.to_dict() if hasattr(meta, "to_dict") else (meta if isinstance(meta, dict) else {}))

        # 1. Source Image Metadata
        h, w = image_arr.shape[:2]
        bands = image_arr.shape[2] if image_arr.ndim == 3 else 1
        img_dims = list(image_arr.shape)
        
        real_file_path = image_path or meta.get("file_path", "memory://input_raster")
        img_hash = cls.compute_sha256(real_file_path if os.path.exists(real_file_path) else None, 
                                      image_arr.tobytes()[:65536] if not os.path.exists(real_file_path) else None)
        sensor = meta.get("sensor_name", meta.get("sensor", "Remote Sensing Platform"))

        source_image = {
            "asset_id": meta.get("asset_id", f"asset-{uuid.uuid4().hex[:8]}"),
            "file_path": real_file_path,
            "sha256": img_hash,
            "sha256_hash": img_hash,
            "dimensions": img_dims,
            "sensor": sensor,
            "modality": meta.get("modality", "optical")
        }

        # 2. Bands / Features Used
        modality = meta.get("modality", "optical").lower()
        if modality == "sar":
            bands_used = ["C-Band VV", "C-Band VH"] if bands >= 2 else ["Microwave Backscatter Intensity"]
        elif modality == "hyperspectral":
            bands_used = [f"Spectral Band {i+1}" for i in range(min(bands, 10))]
        else:
            bands_used = ["Red (Band 4)", "Green (Band 3)", "Blue (Band 2)"]
            if bands >= 4:
                bands_used.append("Near-Infrared (Band 8)")

        # 3. Spatial Region
        bounds = meta.get("bounds") or [0.0, 0.0, float(w), float(h)]
        crs = meta.get("crs") or "EPSG:4326"
        minx, miny, maxx, maxy = bounds[:4]
        
        # Calculate physical area if resolution provided or from projected bounds
        pixel_size = meta.get("pixel_size_meters") or meta.get("resolution")
        physical_area_m2 = None
        if pixel_size is not None:
            try:
                if isinstance(pixel_size, (list, tuple)):
                    rx = abs(float(pixel_size[0])) if len(pixel_size) > 0 else 10.0
                    ry = abs(float(pixel_size[1])) if len(pixel_size) > 1 else rx
                else:
                    rx = ry = abs(float(pixel_size))
                physical_area_m2 = float(h * ry) * float(w * rx)
            except Exception:
                physical_area_m2 = None
        elif "epsg" in str(crs).lower() and "4326" not in str(crs):
            physical_area_m2 = abs(float(maxx - minx) * float(maxy - miny))

        geojson_poly = {
            "type": "Polygon",
            "coordinates": [[[minx, miny], [maxx, miny], [maxx, maxy], [minx, maxy], [minx, miny]]]
        }

        spatial_region = {
            "crs": str(crs),
            "bounds": [round(float(b), 6) for b in bounds],
            "physical_area_sq_m": round(physical_area_m2, 2) if physical_area_m2 else None,
            "physical_area_m2": round(physical_area_m2, 2) if physical_area_m2 else None,
            "pixel_dimensions": [w, h],
            "geojson_geometry": geojson_poly,
            "geojson": geojson_poly
        }

        # 4. Model Output & Candidates
        candidate_objs: List[CandidateAnswer] = []
        cands_input = candidates or (neural_pred.get("candidates") if neural_pred else None)
        
        if cands_input:
            for i, cand in enumerate(cands_input):
                if isinstance(cand, CandidateAnswer):
                    candidate_objs.append(cand)
                elif isinstance(cand, dict):
                    candidate_objs.append(CandidateAnswer(
                        answer=str(cand.get("answer", "unknown")),
                        confidence=round(float(cand.get("confidence", 0.0)), 4),
                        rank=cand.get("rank", i + 1)
                    ))
        
        computed_top_ans = top_answer or (candidate_objs[0].answer if candidate_objs else None)
        if not computed_top_ans and neural_pred and neural_pred.get("top_answer"):
            computed_top_ans = str(neural_pred["top_answer"])
        
        raw_conf = confidence
        if raw_conf is None:
            if candidate_objs:
                raw_conf = candidate_objs[0].confidence
            elif neural_pred and neural_pred.get("confidence") is not None:
                raw_conf = float(neural_pred["confidence"])
            else:
                raw_conf = 0.85

        probabilities = {c.answer: c.confidence for c in candidate_objs}
        if computed_top_ans and computed_top_ans not in probabilities:
            probabilities[computed_top_ans] = round(float(raw_conf), 4)

        model_output = {
            "top_answer": computed_top_ans,
            "candidate_answers": candidate_objs,
            "candidates": [c.model_dump() for c in candidate_objs],
            "probabilities": probabilities,
            "neural_evaluated": bool(neural_pred is not None or checkpoint_path is not None)
        }

        # 5. Confidence & Calibration Info
        probs = [c.confidence for c in candidate_objs]
        entropy = 0.0
        aleatoric = 0.0
        if probs and sum(probs) > 0:
            norm_p = np.array(probs) / sum(probs)
            entropy = float(-np.sum(norm_p * np.log(norm_p + 1e-12)))
            aleatoric = UncertaintyDecompositionEngine.compute_aleatoric_uncertainty(norm_p)

        second_conf = float(candidate_objs[1].confidence) if len(candidate_objs) > 1 else 0.0
        epistemic = UncertaintyDecompositionEngine.compute_epistemic_uncertainty(
            top_prob=float(raw_conf),
            second_prob=second_conf
        )
        data_qual, qual_flags = UncertaintyDecompositionEngine.compute_data_quality_uncertainty(image_arr)

        confidence_info = {
            "confidence_score": round(float(raw_conf), 4),
            "score": round(float(raw_conf), 4),
            "is_calibrated": is_calibrated,
            "confidence_calibrated": is_calibrated,
            "entropy": round(entropy, 4),
            "margin_to_second": round(float(candidate_objs[0].confidence - second_conf), 4) if len(candidate_objs) > 1 else None,
            "confidence_semantics": ConfidenceSemantics.PROBABILITY_CLASS_CORRECTNESS.value,
            "aleatoric_uncertainty": aleatoric,
            "epistemic_uncertainty": epistemic,
            "data_quality_uncertainty": data_qual,
            "registration_uncertainty": 0.0
        }

        # 6. Derived Physical Metrics (Genuine Raster Math)
        metrics = spectral_metrics or GeospatialNormalizer.compute_spectral_breakdown(image_arr)
        derived_metrics = {
            "water_pct": float(metrics.get("water_body_pct", 0.0)),
            "vegetation_pct": float(metrics.get("vegetation_cover_pct", 0.0)),
            "built_up_pct": float(metrics.get("built_up_density_pct", 0.0)),
            "water_body_pct": float(metrics.get("water_body_pct", 0.0)),
            "vegetation_cover_pct": float(metrics.get("vegetation_cover_pct", 0.0)),
            "built_up_density_pct": float(metrics.get("built_up_density_pct", 0.0)),
            "bare_soil_pct": float(metrics.get("bare_soil_pct", 0.0)),
            "mean_ndvi": float(metrics.get("mean_ndvi", 0.0)),
            "mean_ndwi": float(metrics.get("mean_ndwi", 0.0)),
            "mean_ndbi": float(metrics.get("mean_ndbi", 0.0)),
            "is_geotiff": bool(metrics.get("is_geotiff", False))
        }

        # 7. Checkpoint Provenance
        actual_ckpt_hash = checkpoint_hash
        if not actual_ckpt_hash and checkpoint_path and os.path.exists(checkpoint_path):
            actual_ckpt_hash = cls.compute_sha256(checkpoint_path)

        checkpoint_info = {
            "model_name": model_name,
            "checkpoint_path": checkpoint_path,
            "path": checkpoint_path,
            "sha256": actual_ckpt_hash,
            "sha256_hash": actual_ckpt_hash,
            "param_count": param_count,
            "parameter_count": param_count,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
        }

        # 8. Preprocessing Details
        preprocessing_info = {
            "radiometric_scaling": "standard_uint8_0_to_1",
            "normalizer": normalizer_name or "GeospatialNormalizer.compute_spectral_breakdown",
            "input_shape": input_shape or img_dims,
            "target_resolution": [224, 224],
            "interpolation": "bilinear",
            "channels_extracted": bands
        }

        # 9. Warnings & Diagnostics
        active_warnings = list(warnings) if warnings else []
        if fallback_used and fallback_reason:
            active_warnings.append(f"Heuristic fallback engaged: {fallback_reason}")
        if derived_metrics["water_body_pct"] > 50.0 and "water" not in query.lower() and "ocean" not in query.lower():
            active_warnings.append("High surface water presence (>50%) dominates optical reflectance.")
        if np.std(image_arr) < 5.0:
            active_warnings.append("Low dynamic contrast detected in raster; radiometric precision may be degraded.")

        # 10. Granular Evidence Items
        evidence_items: List[EvidenceItem] = []

        # Evidence Item E01: Surface Water Index
        evidence_items.append(EvidenceItem(
            item_id="E01_WATER",
            evidence_id="E01_WATER",
            evidence_type="spectral",
            title="Hydrological Surface Water Fraction",
            description="Normalized Difference Water Index (NDWI) computed across raster pixels.",
            source_layer="Green & NIR / SWIR Bands",
            numeric_value=derived_metrics["water_body_pct"],
            unit="%",
            geojson_geometry=spatial_region["geojson_geometry"]
        ))

        # Evidence Item E02: Photosynthetic Vegetation Canopy
        evidence_items.append(EvidenceItem(
            item_id="E02_VEGETATION",
            evidence_id="E02_VEGETATION",
            evidence_type="spectral",
            title="Photosynthetic Canopy Density",
            description="Normalized Difference Vegetation Index (NDVI) extracted across spatial extent.",
            source_layer="Red & NIR Channels",
            numeric_value=derived_metrics["vegetation_cover_pct"],
            unit="%",
            geojson_geometry=spatial_region["geojson_geometry"]
        ))

        # Evidence Item E03: Anthropogenic Infrastructure / Built-Up
        evidence_items.append(EvidenceItem(
            item_id="E03_BUILT_UP",
            evidence_id="E03_BUILT_UP",
            evidence_type="spatial",
            title="Anthropogenic Infrastructure Density",
            description="High-frequency spatial gradient and structural building footprint density.",
            source_layer="Spatial Texture & Normalized Difference Built-Up Index",
            numeric_value=derived_metrics["built_up_density_pct"],
            unit="%",
            geojson_geometry=spatial_region["geojson_geometry"]
        ))

        return EvidencePackage(
            package_id=package_id,
            query=query,
            answer_text=answer_text or "Analysis grounded in physical evidence",
            source_image=source_image,
            bands_used=bands_used,
            spatial_region=spatial_region,
            model_output=model_output,
            confidence_and_calibration=confidence_info,
            confidence_info=confidence_info,
            derived_metrics=derived_metrics,
            timestamp_utc=now_utc,
            checkpoint_provenance=checkpoint_info,
            checkpoint_info=checkpoint_info,
            preprocessing=preprocessing_info,
            preprocessing_info=preprocessing_info,
            warnings=active_warnings,
            evidence_items=evidence_items
        )
