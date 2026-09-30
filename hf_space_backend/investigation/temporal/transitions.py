"""
TRINETRA Phase 6 — Land-Cover Transition Matrix
Models discrete categorical transitions across multi-epoch observation intervals.
"""

from typing import Dict, Any, List


class LandCoverTransition:
    def __init__(self, from_class: str, to_class: str, confidence: float, area_ha: float):
        self.from_class = from_class
        self.to_class = to_class
        self.confidence = confidence
        self.area_ha = area_ha

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_class": self.from_class,
            "to_class": self.to_class,
            "confidence": round(self.confidence, 3),
            "area_ha": round(self.area_ha, 2),
        }


class TransitionMatrixEngine:
    """
    Computes categorical conversion tables across temporal epochs.
    """

    @classmethod
    def compute_transitions(
        cls,
        epoch_states: List[Dict[str, Any]],
    ) -> List[LandCoverTransition]:
        transitions: List[LandCoverTransition] = []

        if len(epoch_states) < 2:
            return transitions

        for i in range(len(epoch_states) - 1):
            s0 = epoch_states[i]
            s1 = epoch_states[i + 1]

            c0 = s0.get("class", "VEGETATION")
            c1 = s1.get("class", "BUILT_UP")
            area = s1.get("area_ha", 1.0)
            conf = min(s0.get("confidence", 0.8), s1.get("confidence", 0.8))

            transitions.append(
                LandCoverTransition(
                    from_class=c0,
                    to_class=c1,
                    confidence=conf,
                    area_ha=area,
                )
            )

        return transitions
