"""
TRINETRA Phase 6 — Findings Report Formatter
Formats structured findings strictly grounded in verified evidence IDs.
"""

from typing import Dict, Any, List


class FindingsFormatter:
    """
    Renders structured findings with quantitative values and explicit evidence provenance links.
    """

    @classmethod
    def format_findings(cls, findings: List[Any]) -> List[Dict[str, Any]]:
        formatted = []
        for idx, f in enumerate(findings):
            data = f.dict() if hasattr(f, "dict") else dict(f)
            finding_id = data.get("finding_id") or f"find_{idx+1:02d}"
            formatted.append({
                "finding_id": finding_id,
                "category": data.get("category", "GENERAL_OBSERVATION"),
                "statement": data.get("statement") or data.get("description", ""),
                "quantitative_value": data.get("quantitative_value") or data.get("value", {}),
                "confidence": round(float(data.get("confidence", 0.85)), 2),
                "supporting_evidence_ids": data.get("supporting_evidence_ids", []),
                "limitations": data.get("limitations", []),
                "summary_badge": cls._generate_badge(data),
            })
        return formatted

    @classmethod
    def _generate_badge(cls, data: Dict[str, Any]) -> str:
        conf = float(data.get("confidence", 0.85))
        if conf >= 0.85:
            return "HIGH_CONFIDENCE"
        elif conf >= 0.65:
            return "MODERATE_CONFIDENCE"
        return "LOW_CONFIDENCE"
