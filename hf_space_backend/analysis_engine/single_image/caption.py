"""
TRINETRA Analysis Engine — Caption Specialist Adapter
Adapts the existing RSCaptionSpecialist to the Explore Analysis Engine.
"""

from typing import Dict, Any, Optional
import numpy as np
from services.captioning.captioning_service import RSCaptionSpecialist


class CaptionSpecialistAdapter:
    def __init__(self):
        self.specialist = RSCaptionSpecialist()

    def generate_caption(
        self,
        image_arr: np.ndarray,
        meta: Dict[str, Any],
        query: str = "Describe this scene.",
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generates rich scene captioning and spectral breakdown via RSCaptionSpecialist.
        """
        params = parameters or {}
        return self.specialist.execute(
            image_arr=image_arr,
            meta=meta,
            query=query,
            parameters=params,
        )
