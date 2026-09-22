"""
TRINETRA Phase 6 — Investigation Provenance
Deterministic SHA-256 provenance tracking for end-to-end auditability and reproducibility.
"""

import hashlib
import json
from typing import Dict, Any, List, Optional
from config.settings import settings


class InvestigationProvenanceTracker:
    @classmethod
    def generate_provenance(
        cls,
        investigation_id: str,
        question: str,
        observation_ids: List[str],
        specialists: List[str],
        evidence_count: int,
        model_versions: Dict[str, str],
        preprocessing_meta: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Computes a deterministic SHA-256 processing hash binding all investigation factors.
        """
        payload = {
            "app_version": settings.app_version,
            "investigation_id": investigation_id,
            "question": question.strip(),
            "observation_ids": sorted(observation_ids),
            "specialists": sorted(specialists),
            "evidence_count": evidence_count,
            "model_versions": model_versions,
            "preprocessing": preprocessing_meta,
            "config_hash": settings.get_config_hash(),
        }

        serialized = json.dumps(payload, sort_keys=True)
        processing_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        return {
            "processing_hash": processing_hash,
            "investigation_id": investigation_id,
            "app_version": settings.app_version,
            "observation_ids": observation_ids,
            "specialists_invoked": specialists,
            "evidence_count": evidence_count,
            "model_versions": model_versions,
            "reproducible": True,
        }

    @classmethod
    def compute_processing_hash(
        cls,
        observation_ids: List[str],
        specialist_versions: Optional[Dict[str, str]] = None,
        pipeline_config: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> str:
        payload = {
            "observation_ids": sorted(observation_ids),
            "specialist_versions": specialist_versions or {},
            "pipeline_config": pipeline_config or {},
            "app_version": getattr(settings, "app_version", "6.0.0"),
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
