"""
TRINETRA Phase 7 — Similarity Scoring
Computes explainable cosine distance and generates human-readable comparison rationales.
"""

import math
from typing import List, Tuple
from intelligence.similarity.fingerprint import EOFingerprint


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a, b in zip(v1, v2)))
    norm2 = math.sqrt(sum(b * b for a, b in zip(v1, v2)))
    if norm1 <= 0.0 or norm2 <= 0.0:
        return 0.0
    return max(0.0, min(1.0, dot / (norm1 * norm2)))


class SimilarityScorer:
    """
    Evaluates multi-attribute similarity with transparent match justifications.
    """

    @classmethod
    def compare_fingerprints(
        cls,
        target: EOFingerprint,
        candidate: EOFingerprint,
    ) -> Tuple[float, str, List[str]]:
        factors: List[str] = []

        # Vector cosine similarity
        vector_sim = cosine_similarity(target.vector, candidate.vector)

        # Semantic class compatibility bonus
        same_class = target.semantic_class.upper() == candidate.semantic_class.upper()
        if same_class:
            factors.append(f"Same semantic class: {target.semantic_class.replace('_', ' ').lower()}")
            total_score = (0.65 * vector_sim) + 0.35
        else:
            total_score = 0.65 * vector_sim

        # Area comparison
        area_diff = abs(target.area_ha - candidate.area_ha)
        if area_diff <= max(2.0, target.area_ha * 0.30):
            factors.append(f"Comparable spatial scale ({round(candidate.area_ha, 1)} ha vs {round(target.area_ha, 1)} ha)")

        # Temporal persistence comparison
        persist_diff = abs(target.persistence_score - candidate.persistence_score)
        if persist_diff <= 0.20:
            factors.append("Consistent temporal persistence profile")

        score = round(min(1.0, max(0.05, total_score)), 3)

        if score >= 0.75:
            level = "High"
        elif score >= 0.50:
            level = "Medium"
        else:
            level = "Low"

        if not factors:
            factors.append("Statistical feature vector alignment")

        return score, level, factors
