"""
TRINETRA Phase 8 — Finding Clusterer
Groups and synthesizes findings by geographic region, sensor modality, and confidence grade.
"""

from typing import Dict, Any, List
from collections import defaultdict


class FindingClusterer:
    """
    Partitions findings into analytical categories for synthesis.
    """

    @classmethod
    def cluster_by_modality(cls, findings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        clusters = defaultdict(list)
        for f in findings:
            sensor = f.get("sensor_type", f.get("modality", "OPTICAL")).upper()
            clusters[sensor].append(f)
        return dict(clusters)

    @classmethod
    def cluster_by_region(cls, findings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        clusters = defaultdict(list)
        for f in findings:
            reg = f.get("region_id", "GLOBAL")
            clusters[reg].append(f)
        return dict(clusters)

    @classmethod
    def grade_confidence(cls, findings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        grades = {"HIGH": [], "MEDIUM": [], "LOW": []}
        for f in findings:
            conf = float(f.get("confidence", 0.7))
            if conf >= 0.85:
                grades["HIGH"].append(f)
            elif conf >= 0.70:
                grades["MEDIUM"].append(f)
            else:
                grades["LOW"].append(f)
        return grades
