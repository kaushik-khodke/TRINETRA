"""
TRINETRA Analysis Engine — Provenance & Reproducibility
Binds every run to a deterministic SHA-256 processing hash calculated from
AOI geometry, input observation hashes, model versions, thresholds, and parameters.
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from config.settings import settings


class ProvenanceTracker:
    @staticmethod
    def compute_processing_hash(
        aoi_hash: str,
        observation_ids: List[str],
        mode: str,
        model_version: str,
        threshold: float,
        preprocessing_config: Dict[str, Any],
    ) -> str:
        """
        Creates a deterministic SHA-256 hash identifying this exact analytical configuration.
        """
        payload = {
            "app_version": settings.app_version,
            "aoi_hash": aoi_hash,
            "observation_ids": sorted(observation_ids),
            "mode": mode,
            "model_version": model_version,
            "threshold": round(threshold, 4),
            "preprocessing": sorted(preprocessing_config.items()),
            "seed": settings.seed,
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def build_provenance_manifest(
        run_id: str,
        mode: str,
        observation_ids: List[str],
        aoi_hash: Optional[str],
        crs: str,
        resolution_meters: float,
        preprocessing_summary: Dict[str, Any],
        model_metadata: Dict[str, Any],
        threshold: float,
        evidence_count: int,
        finding_count: int,
        execution_time_seconds: float,
    ) -> Dict[str, Any]:
        """
        Assembles a comprehensive, auditable provenance manifest.
        """
        proc_hash = ProvenanceTracker.compute_processing_hash(
            aoi_hash=aoi_hash or "global",
            observation_ids=observation_ids,
            mode=mode,
            model_version=model_metadata.get("version", "1.0.0"),
            threshold=threshold,
            preprocessing_config=preprocessing_summary,
        )

        return {
            "run_id": run_id,
            "processing_hash": proc_hash,
            "app_version": settings.app_version,
            "mode": mode,
            "timestamp_utc": datetime.utcnow().isoformat(),
            "inputs": {
                "observation_ids": observation_ids,
                "aoi_hash": aoi_hash,
                "crs": crs,
                "resolution_meters": resolution_meters,
            },
            "preprocessing": preprocessing_summary,
            "models": {
                "name": model_metadata.get("name", "TRINETRA_EO_Specialist"),
                "version": model_metadata.get("version", "1.0.0"),
                "weights_hash": model_metadata.get("weights_hash", "active_native"),
                "device": settings.device,
                "precision": settings.precision,
            },
            "parameters": {
                "threshold": threshold,
                "min_region_pixels": settings.analysis_min_region_pixels,
                "tile_size": settings.analysis_tile_size,
                "tile_overlap": settings.analysis_tile_overlap,
            },
            "results_summary": {
                "evidence_count": evidence_count,
                "finding_count": finding_count,
                "execution_time_seconds": round(execution_time_seconds, 3),
            },
        }
