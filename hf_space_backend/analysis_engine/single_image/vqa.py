"""
TRINETRA Analysis Engine — VQA Specialist Adapter
Adapts the existing RSVqaSpecialist to the Explore Analysis Engine.
"""

from typing import Dict, Any, Optional
import numpy as np
from services.vqa.vqa_service import RSVqaSpecialist


class VqaSpecialistAdapter:
    def __init__(self):
        self.specialist = RSVqaSpecialist()

    def answer_question(
        self,
        image_arr: np.ndarray,
        meta: Dict[str, Any],
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes domain VQA via the registered RSVqaSpecialist.
        """
        params = parameters or {}
        return self.specialist.execute(
            image_arr=image_arr,
            meta=meta,
            query=query,
            parameters=params,
        )
