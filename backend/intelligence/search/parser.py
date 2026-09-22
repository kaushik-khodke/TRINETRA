"""
TRINETRA Phase 7 — Search Query Parser
Deterministic fast-path parser extracting structured constraints from natural-language queries.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from intelligence.search.semantic import SemanticSearchMatcher


class SearchQueryParser:
    """
    Safely translates human queries into structured filter parameters.
    Bypasses LLM for deterministic queries to guarantee zero latency and zero hallucination.
    """

    STATE_MAPPINGS = {
        "persistent": "PERSISTENT",
        "corroborated": "CORROBORATED",
        "candidate": "CANDIDATE",
        "resolved": "RESOLVED",
        "unresolved": "CANDIDATE",
        "ongoing": "PERSISTENT",
        "active": "PERSISTENT",
    }

    CONFIDENCE_MAPPINGS = {
        "high confidence": 0.75,
        "medium confidence": 0.50,
        "reliable": 0.70,
        "verified": 0.80,
    }

    @classmethod
    def parse_query(cls, raw_query: Optional[str]) -> Dict[str, Any]:
        filters: Dict[str, Any] = {
            "semantic_class": None,
            "state": None,
            "min_confidence": None,
            "temporal_range": None,
            "cross_modal_only": False,
            "sanitized_query": "",
        }

        if not raw_query:
            return filters

        # Strip hazardous characters (SQL/shell injection guard)
        sanitized = re.sub(r"[;'\"`\\<>{}]", "", raw_query).strip()
        filters["sanitized_query"] = sanitized
        q_lower = sanitized.lower()

        # 1. Semantic class extraction
        s_class = SemanticSearchMatcher.infer_semantic_class(q_lower)
        if s_class:
            filters["semantic_class"] = s_class

        # 2. Event lifecycle state extraction
        for kw, state in cls.STATE_MAPPINGS.items():
            if kw in q_lower:
                filters["state"] = state
                break

        # 3. Confidence requirement extraction
        for kw, conf in cls.CONFIDENCE_MAPPINGS.items():
            if kw in q_lower:
                filters["min_confidence"] = conf
                break

        # 4. Modality / cross-modal check
        if "sar" in q_lower or "radar" in q_lower or "cross-modal" in q_lower or "cross modal" in q_lower:
            filters["cross_modal_only"] = True

        # 5. Temporal scope extraction
        now = datetime.utcnow()
        if "last year" in q_lower or "past year" in q_lower:
            start_date = (now - timedelta(days=365)).isoformat()
            filters["temporal_range"] = {"start_date": start_date, "end_date": now.isoformat()}
        elif "last 6 months" in q_lower or "past six months" in q_lower:
            start_date = (now - timedelta(days=180)).isoformat()
            filters["temporal_range"] = {"start_date": start_date, "end_date": now.isoformat()}
        elif "last 3 months" in q_lower or "past quarter" in q_lower:
            start_date = (now - timedelta(days=90)).isoformat()
            filters["temporal_range"] = {"start_date": start_date, "end_date": now.isoformat()}
        elif "last month" in q_lower or "past month" in q_lower:
            start_date = (now - timedelta(days=30)).isoformat()
            filters["temporal_range"] = {"start_date": start_date, "end_date": now.isoformat()}

        return filters
