"""
TRINETRA Analysis Engine — Execution Router
Directs the planned analysis request to the designated specialist pipeline.
Enforces mutual exclusivity so that only the selected analytical mode is run.
"""

from typing import Dict, Any
from analysis_engine.schemas import AnalysisMode
from analysis_engine.context import AnalysisContext
from analysis_engine.errors import InputFailureError


class AnalysisRouter:
    @staticmethod
    def route_execution(
        context: AnalysisContext,
        change_service: Any,
        sar_optical_service: Any,
        single_image_service: Any,
    ) -> Dict[str, Any]:
        """
        Executes the mutually exclusive pipeline based on context.mode.
        """
        mode = context.mode

        if mode == AnalysisMode.BI_TEMPORAL.value:
            return change_service.execute_pipeline(context)

        elif mode == AnalysisMode.SAR_OPTICAL.value:
            return sar_optical_service.execute_pipeline(context)

        elif mode == AnalysisMode.SINGLE_IMAGE.value:
            return single_image_service.execute_pipeline(context)

        else:
            raise InputFailureError(f"Unsupported analysis mode for routing: {mode}")
