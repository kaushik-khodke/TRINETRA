"""
TRINETRA Phase 7 — Semantic Query Matcher
Maps natural-language query terms to canonical EO taxonomy classes.
"""

from typing import Optional, List


class SemanticSearchMatcher:
    """
    Interprets analytical intent and matches query concepts to canonical semantic categories.
    """

    KEYWORD_MAPPINGS = {
        "BUILT_UP_EXPANSION": ["built-up", "built up", "urban", "construction", "settlement", "structure", "building", "expansion"],
        "VEGETATION_LOSS": ["vegetation", "forest", "tree", "canopy", "deforestation", "clearing", "agriculture", "crop"],
        "WATER_BODY_DYNAMICS": ["water", "flood", "lake", "river", "reservoir", "submergence", "inundation"],
        "SURFACE_INFRASTRUCTURE": ["road", "runway", "highway", "pavement", "tarmac", "industrial", "facility"],
    }

    @classmethod
    def infer_semantic_class(cls, query: str) -> Optional[str]:
        if not query:
            return None
        q_lower = query.lower()
        for s_class, keywords in cls.KEYWORD_MAPPINGS.items():
            if any(kw in q_lower for kw in keywords):
                return s_class
        return None

    @classmethod
    def matches_semantic(cls, candidate_class: str, target_class: Optional[str]) -> bool:
        if not target_class or target_class.upper() in ("ALL", "GENERAL_CHANGE"):
            return True
        c_norm = candidate_class.upper().replace("-", "_").replace(" ", "_")
        t_norm = target_class.upper().replace("-", "_").replace(" ", "_")
        if c_norm == t_norm:
            return True
        if c_norm in t_norm or t_norm in c_norm:
            return True
        # Check taxonomy keywords
        for s_class, keywords in cls.KEYWORD_MAPPINGS.items():
            kws = [kw.upper().replace("-", "_").replace(" ", "_") for kw in keywords]
            if (t_norm == s_class or any(k in t_norm for k in kws)) and (c_norm == s_class or any(k in c_norm for k in kws)):
                return True
        return False

