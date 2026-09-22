"""
TRINETRA Phase 7 — Intelligence Provenance & Fingerprinting
Computes deterministic SHA-256 hashes for findings, events, baselines, and duplicate alert suppression.
"""

import hashlib
import json
from typing import Dict, Any, List, Optional


class IntelligenceProvenance:
    """
    Deterministic cryptographic hasher ensuring tamper-evident provenance and idempotent ingestion.
    """

    @classmethod
    def compute_finding_fingerprint(
        cls,
        investigation_id: str,
        semantic_class: str,
        bounding_box: Optional[List[float]],
        metrics: Dict[str, Any],
    ) -> str:
        payload = {
            "investigation_id": investigation_id,
            "semantic_class": semantic_class,
            "bounding_box": [round(c, 4) for c in (bounding_box or [])],
            "metrics": {k: round(v, 4) if isinstance(v, (int, float)) else str(v) for k, v in sorted(metrics.items())},
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def compute_event_fingerprint(
        cls,
        canonical_region_id: str,
        semantic_class: str,
        observation_ids: List[str],
    ) -> str:
        payload = {
            "canonical_region_id": canonical_region_id,
            "semantic_class": semantic_class,
            "observation_ids": sorted(observation_ids),
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def compute_alert_fingerprint(
        cls,
        monitor_id: str,
        event_id: Optional[str],
        observation_id: str,
        condition_hash: str,
    ) -> str:
        payload = {
            "monitor_id": monitor_id,
            "event_id": event_id or "none",
            "observation_id": observation_id,
            "condition_hash": condition_hash,
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def compute_search_hash(
        cls,
        query: Optional[str],
        filters: Dict[str, Any],
        index_version: str = "v1.0",
    ) -> str:
        payload = {
            "query": (query or "").strip().lower(),
            "filters": {k: str(v) for k, v in sorted(filters.items())},
            "index_version": index_version,
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @classmethod
    def compute_baseline_hash(
        cls,
        metric_name: str,
        spatial_unit: str,
        temporal_window: str,
        version: str = "v1.0",
    ) -> str:
        payload = {
            "metric_name": metric_name,
            "spatial_unit": spatial_unit,
            "temporal_window": temporal_window,
            "version": version,
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
