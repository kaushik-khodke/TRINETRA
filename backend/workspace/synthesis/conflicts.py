"""
TRINETRA Phase 8 — Analytical Conflict Detector
Identifies contradictory findings, sensor modality divergence, and temporal ambiguities.
"""

import uuid
from typing import Dict, Any, List, Optional


class ConflictRecord:
    def __init__(
        self,
        conflict_id: str,
        entity_a_id: str,
        entity_b_id: str,
        conflict_type: str,
        description: str,
        severity: str = "MEDIUM",
    ):
        self.conflict_id = conflict_id
        self.entity_a_id = entity_a_id
        self.entity_b_id = entity_b_id
        self.conflict_type = conflict_type  # MODALITY_DIVERGENCE, TREND_OPPOSITION, CONFIDENCE_DISPARITY
        self.description = description
        self.severity = severity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "entity_a_id": self.entity_a_id,
            "entity_b_id": self.entity_b_id,
            "conflict_type": self.conflict_type,
            "description": self.description,
            "severity": self.severity,
        }


class ConflictDetector:
    """
    Scans candidate findings, observations, and board items to pinpoint contradictions.
    """

    @classmethod
    def detect_conflicts(
        cls,
        findings: List[Dict[str, Any]],
        relations: Optional[List[Dict[str, Any]]] = None,
    ) -> List[ConflictRecord]:
        conflicts: List[ConflictRecord] = []

        # 1. Check explicit "contradicts" relations from evidence board
        if relations:
            for rel in relations:
                if rel.get("relation_type") == "contradicts":
                    conflicts.append(
                        ConflictRecord(
                            conflict_id=f"conf-{uuid.uuid4().hex[:8]}",
                            entity_a_id=rel.get("source_item_id", ""),
                            entity_b_id=rel.get("target_item_id", ""),
                            conflict_type="ANALYST_DECLARED_CONTRADICTION",
                            description=rel.get("metadata", {}).get(
                                "reason", "Analyst identified an explicit contradiction between these items."
                            ),
                            severity="HIGH",
                        )
                    )

        # 2. Automated heuristic check: Opposing change directions in the same region
        for i in range(len(findings)):
            for j in range(i + 1, len(findings)):
                f1 = findings[i]
                f2 = findings[j]
                same_region = f1.get("region_id") and f1.get("region_id") == f2.get("region_id")
                if same_region:
                    change_1 = f1.get("metrics", {}).get("change_pct", 0.0)
                    change_2 = f2.get("metrics", {}).get("change_pct", 0.0)
                    # Significant opposing signs
                    if (change_1 > 10.0 and change_2 < -10.0) or (change_1 < -10.0 and change_2 > 10.0):
                        conflicts.append(
                            ConflictRecord(
                                conflict_id=f"conf-{uuid.uuid4().hex[:8]}",
                                entity_a_id=f1.get("finding_id", str(i)),
                                entity_b_id=f2.get("finding_id", str(j)),
                                conflict_type="TREND_OPPOSITION",
                                description=(
                                    f"Opposing trend metrics detected in region {f1.get('region_id')}: "
                                    f"Finding {f1.get('finding_id')} ({change_1:+.1f}%) vs "
                                    f"Finding {f2.get('finding_id')} ({change_2:+.1f}%)."
                                ),
                                severity="HIGH",
                            )
                        )

        return conflicts
