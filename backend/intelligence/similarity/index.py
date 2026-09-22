"""
TRINETRA Phase 7 — Abstract Similarity Index
Modular vector abstraction supporting local lightweight search without requiring massive vector database dependencies.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
from intelligence.similarity.fingerprint import EOFingerprint
from intelligence.similarity.similarity import SimilarityScorer


class SimilarityIndex(ABC):
    """
    Abstract contract for vector and fingerprint retrieval.
    """

    @abstractmethod
    def insert(self, entity_id: str, fingerprint: EOFingerprint) -> None:
        pass

    @abstractmethod
    def search(
        self,
        target_fingerprint: EOFingerprint,
        top_k: int = 10,
        min_threshold: float = 0.40,
    ) -> List[Tuple[str, float, str, List[str]]]:
        """Returns list of (entity_id, score, similarity_level, match_factors)."""
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        pass


class LocalSimilarityIndex(SimilarityIndex):
    """
    High-performance in-memory index suitable for hackathon, desktop, and embedded operation.
    """

    def __init__(self):
        self._index: Dict[str, EOFingerprint] = {}

    def insert(self, entity_id: str, fingerprint: EOFingerprint) -> None:
        self._index[entity_id] = fingerprint

    def search(
        self,
        target_fingerprint: EOFingerprint,
        top_k: int = 10,
        min_threshold: float = 0.40,
    ) -> List[Tuple[str, float, str, List[str]]]:
        candidates: List[Tuple[str, float, str, List[str]]] = []

        for eid, cand_fp in self._index.items():
            if eid == target_fingerprint.entity_id:
                continue

            score, level, factors = SimilarityScorer.compare_fingerprints(target_fingerprint, cand_fp)
            if score >= min_threshold:
                candidates.append((eid, score, level, factors))

        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_k]

    def delete(self, entity_id: str) -> bool:
        if entity_id in self._index:
            del self._index[entity_id]
            return True
        return False

    def clear(self) -> None:
        self._index.clear()


# Default singleton instance
similarity_index = LocalSimilarityIndex()
