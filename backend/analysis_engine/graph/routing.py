"""
TRINETRA Analysis Engine — LangGraph Routing Functions
Controls conditional branching between analytical pipelines.
"""

from typing import Literal
from analysis_engine.graph.state import AnalysisGraphState


def route_analysis_mode(
    state: AnalysisGraphState,
) -> Literal["run_change_analysis", "run_sar_optical", "run_single_image", "error"]:
    """Selects the mutually exclusive specialist node based on state['mode']."""
    if state.get("error"):
        return "error"

    mode = state.get("mode", "BI_TEMPORAL").upper()
    if mode == "BI_TEMPORAL":
        return "run_change_analysis"
    elif mode == "SAR_OPTICAL":
        return "run_sar_optical"
    elif mode == "SINGLE_IMAGE":
        return "run_single_image"
    return "run_change_analysis"
