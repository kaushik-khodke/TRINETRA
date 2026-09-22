"""
TRINETRA Phase 6 — Evidence Validator & Conflict Detection
Explicitly identifies and preserves discrepancies between sensor modalities and analytical outputs.
"""

from typing import Dict, Any, List, Tuple
from investigation.evidence.models import EvidenceItem, EvidenceType
from investigation.schemas import EvidenceConflict


class EvidenceConflictValidator:
    """
    Scans evidence collections to detect unresolved contradictions between modalities.
    """

    @classmethod
    def find_conflicts(cls, evidence_items: List[EvidenceItem]) -> List[EvidenceConflict]:
        conflicts: List[EvidenceConflict] = []

        # Group items by region_id
        by_region: Dict[str, List[EvidenceItem]] = {}
        for item in evidence_items:
            rid = item.metadata.get("region_id", "global")
            if rid not in by_region:
                by_region[rid] = []
            by_region[rid].append(item)

        for rid, items in by_region.items():
            optical_changes = [it for it in items if it.type in [EvidenceType.CHANGE, EvidenceType.OPTICAL]]
            sar_items = [it for it in items if it.type == EvidenceType.SAR]

            # Case: Strong Optical change vs weak/zero SAR delta
            for opt in optical_changes:
                for sar in sar_items:
                    if isinstance(opt.value, dict):
                        opt_val = float(opt.value.get("change_percentage", 0.0)) / 100.0 if "change_percentage" in opt.value else opt.confidence
                    elif isinstance(opt.value, (int, float)):
                        opt_val = float(opt.value)
                    else:
                        opt_val = opt.confidence

                    if isinstance(sar.value, dict):
                        sar_val = abs(float(sar.value.get("delta_sigma0_db", 0.0)))
                    elif isinstance(sar.value, (int, float)):
                        sar_val = abs(float(sar.value))
                    else:
                        sar_val = sar.confidence

                    if opt_val >= 0.05 and sar_val < 0.5:
                        conflicts.append(
                            EvidenceConflict(
                                conflict_id=f"cnf_{opt.id}_{sar.id}",
                                evidence_a_id=opt.id,
                                evidence_b_id=sar.id,
                                modality_a="OPTICAL",
                                evidence_a=f"Optical change detected ({opt.id})",
                                modality_b="SAR",
                                evidence_b=f"SAR microwave response weak ({sar.id})",
                                conflict_type="OPTICAL_SAR_DISCREPANCY",
                                severity="medium",
                                description=(
                                    "Optical surface reflectance indicates physical surface transformation, "
                                    "but microwave C-band backscatter did not exhibit structural roughness elevation."
                                ),
                                explanation=(
                                    "Optical surface reflectance indicates significant transformation, "
                                    "but microwave C-band backscatter did not exhibit structural roughness elevation. "
                                    "May indicate flat surface clearing, low-dielectric disturbance, or soil moisture variations."
                                ),
                                resolution_strategy="Preserve both signatures without averaging away discrepancy.",
                                status="unresolved",
                            )
                        )

        return conflicts

    detect_conflicts = find_conflicts
