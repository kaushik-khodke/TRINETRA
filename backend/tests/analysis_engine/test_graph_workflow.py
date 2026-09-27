"""
Unit tests for Explore Analysis LangGraph Workflow, Node Execution, and Conditional Routing.
"""

import numpy as np
import pytest
from analysis_engine.graph.state import AnalysisGraphState
from analysis_engine.graph.workflow import analysis_graph
from analysis_engine.graph.nodes import (
    validate_request_node,
    prepare_assets_node,
    preprocess_node,
    run_change_analysis_node,
    validate_evidence_node,
)


def test_individual_nodes():
    # 1. Validate request node
    s1 = validate_request_node({"query": "What changed?"})
    assert s1.get("mode") == "BI_TEMPORAL"

    # 2. Prepare assets node
    s2 = prepare_assets_node({})
    assert s2.get("aoi_bounds") is not None

    # 3. Preprocess node
    s3 = preprocess_node({"tensors": {}})
    assert "arr_a" in s3["tensors"]
    assert "arr_b" in s3["tensors"]

    # 4. Change analysis node
    s4 = run_change_analysis_node({
        "run_id": "test_node_run",
        "query": "Detect changes",
        "aoi_bounds": [79.0, 21.0, 79.1, 21.1],
        "tensors": s3["tensors"],
    })
    assert "evidence_pack" in s4

    # 5. Validate evidence node
    s5 = validate_evidence_node({"evidence_pack": s4["evidence_pack"]})
    assert s5.get("evidence_valid") is True


def test_full_langgraph_execution_bi_temporal():
    """Runs the compiled LangGraph from entrypoint to END."""
    initial_state = {
        "run_id": "test_graph_bitemporal",
        "request_id": "req_01",
        "query": "Identify new structures between observations",
        "mode": "BI_TEMPORAL",
        "observation_ids": ["obs_01", "obs_02"],
        "aoi_bounds": [79.0, 21.0, 79.1, 21.1],
        "tensors": {
            "arr_a": np.zeros((100, 100, 3), dtype=np.float32),
            "arr_b": np.zeros((100, 100, 3), dtype=np.float32),
        },
    }

    final_state = analysis_graph.invoke(initial_state)

    assert "evidence_pack" in final_state
    assert "narrative" in final_state
    assert "artifacts" in final_state
    assert "provenance_manifest" in final_state
