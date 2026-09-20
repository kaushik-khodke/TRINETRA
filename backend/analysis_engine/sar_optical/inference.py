"""
TRINETRA Analysis Engine — SAR-Optical Specialist Adapter
Adapts the existing OpticalSarFusionSpecialist to the Explore Analysis Engine.
"""

from typing import Dict, Any, List, Optional
import numpy as np
from services.optical_sar.optical_sar_service import OpticalSarFusionSpecialist


class CrossModalSpecialistAdapter:
    def __init__(self):
        self.specialist = OpticalSarFusionSpecialist()

    def run_inference(
        self,
        opt_arr: np.ndarray,
        sar_arr: np.ndarray,
        opt_meta: Dict[str, Any],
        sar_meta: Dict[str, Any],
        query: str = "Analyze this region using SAR and optical imagery.",
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes cross-modal joint reasoning via the registered OpticalSarFusionSpecialist.
        """
        params = parameters or {}
        return self.specialist.execute(
            images_arr=[opt_arr, sar_arr],
            metas=[opt_meta, sar_meta],
            query=query,
            parameters=params,
        )
