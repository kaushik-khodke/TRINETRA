"""
TRINETRA Phase 6 — Tests for Full LangGraph Investigation Workflow
"""

import pytest
import os
from investigation.graph.workflow import investigation_graph
from investigation.models import InvestigationStatus


def test_investigation_graph_full_execution():
    initial_state = {
        "investigation_id": "inv_test_graph_01",
        "question": "What physical changes occurred in this area? Was it built-up expansion?",
        "observation_ids": ["obs_a", "obs_b"],
        "aoi": {
            "type": "Polygon",
            "coordinates": [[[79.088, 21.145], [79.112, 21.145], [79.112, 21.165], [79.088, 21.165], [79.088, 21.145]]],
        },
        "status": "QUEUED",
        "warnings": [],
        "errors": [],
    }

    final_state = investigation_graph.invoke(initial_state)

    assert final_state["status"] == "COMPLETED"
    assert "plan" in final_state
    assert len(final_state.get("evidence_items", [])) > 0
    assert len(final_state.get("findings", [])) > 0
    assert len(final_state.get("hypotheses", [])) > 0
    assert "conclusion" in final_state
    assert "summary" in final_state["conclusion"]
    assert "attribution_boundary" in final_state["conclusion"]
    assert len(final_state.get("artifacts", [])) > 0
