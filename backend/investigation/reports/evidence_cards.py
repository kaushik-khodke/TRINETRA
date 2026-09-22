"""
TRINETRA Phase 6 — Evidence Card Formatter
Renders modular cards for UI visualization with sensor badges, measurement values,
spatial references, and relationship indicators.
"""

from typing import Dict, Any, List, Optional, Set


class EvidenceCardFormatter:
    """
    Transforms raw EvidenceItems into human-readable, interactive cards.
    """

    @classmethod
    def format_cards(
        cls,
        evidence_items: List[Any],
        relationships: Optional[List[Any]] = None,
        conflicts: Optional[List[Any]] = None,
    ) -> List[Dict[str, Any]]:
        rel_counts: Dict[str, int] = {}
        if relationships:
            for r in relationships:
                src = r.source_id if hasattr(r, "source_id") else r.get("source_id")
                tgt = r.target_id if hasattr(r, "target_id") else r.get("target_id")
                if src:
                    rel_counts[src] = rel_counts.get(src, 0) + 1
                if tgt:
                    rel_counts[tgt] = rel_counts.get(tgt, 0) + 1

        conflict_ids = set()
        if conflicts:
            for c in conflicts:
                e1 = c.evidence_a_id if hasattr(c, "evidence_a_id") else c.get("evidence_a_id")
                e2 = c.evidence_b_id if hasattr(c, "evidence_b_id") else c.get("evidence_b_id")
                if e1:
                    conflict_ids.add(e1)
                if e2:
                    conflict_ids.add(e2)

        cards = []
        for item in evidence_items:
            data = item.to_dict() if hasattr(item, "to_dict") else (item.dict() if hasattr(item, "dict") else dict(item))
            eid = data.get("id", "")
            cards.append({
                "id": eid,
                "type": data.get("type", "METADATA"),
                "source": data.get("source", "specialist"),
                "observation_ids": data.get("observation_ids", []),
                "confidence": round(float(data.get("confidence", 1.0)), 2),
                "quality": round(float(data.get("quality", 1.0)), 2),
                "value": data.get("value"),
                "bounding_box": data.get("bounding_box"),
                "geometry": data.get("geometry"),
                "relationship_count": rel_counts.get(eid, 0),
                "has_conflict": eid in conflict_ids,
                "metadata": data.get("metadata", {}),
            })
        return cards
