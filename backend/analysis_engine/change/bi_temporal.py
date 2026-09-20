"""
TRINETRA Analysis Engine — Bi-Temporal Specialist Adapter
Adapts the existing BiTemporalChangeSpecialist (change_ai) to the Explore Analysis Engine.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from services.change.change_service import BiTemporalChangeSpecialist


class BiTemporalSpecialistAdapter:
    def __init__(self):
        self.specialist = BiTemporalChangeSpecialist()

    def run_inference(
        self,
        arr_t1: np.ndarray,
        arr_t2: np.ndarray,
        meta_t1: Dict[str, Any],
        meta_t2: Dict[str, Any],
        query: str = "What changed between these observations?",
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes change inference via the registered BiTemporalChangeSpecialist.
        """
        params = parameters or {}
        return self.specialist.execute(
            images_arr=[arr_t1, arr_t2],
            metas=[meta_t1, meta_t2],
            query=query,
            parameters=params,
        )
