"""
TRINETRA Phase 6 — Tests for Investigation Planner
"""

import pytest
from investigation.schemas import InvestigationRequest
from investigation.planner import InvestigationPlanner


def test_planner_intent_built_up():
    req = InvestigationRequest(
        question="Detect new construction and building expansion in this region",
        observation_ids=["obs_1", "obs_2"],
    )
    plan = InvestigationPlanner.plan(req)
    assert plan["intent"] == "BUILT_UP_CHANGE"
    assert "change_detection" in plan["planned_specialists"]
    assert "grounding" in plan["planned_specialists"]
    assert plan["estimated_cost"] in ["LOW", "MEDIUM", "HIGH"]
    assert plan["estimated_runtime_seconds"] > 0


def test_planner_intent_vegetation():
    req = InvestigationRequest(
        question="Analyze forest canopy loss and deforestation trends",
        observation_ids=["obs_1"],
    )
    plan = InvestigationPlanner.plan(req)
    assert plan["intent"] == "VEGETATION_CHANGE"
    assert "spectral_analysis" in plan["planned_specialists"]


def test_planner_intent_sar_multimodal():
    req = InvestigationRequest(
        question="Evaluate cross-modal microwave SAR and optical data for surface changes",
        observation_ids=["obs_1", "obs_2"],
    )
    plan = InvestigationPlanner.plan(req)
    assert plan["intent"] == "MULTIMODAL_CHANGE"
    assert "sar_analysis" in plan["planned_specialists"]


def test_planner_validation_valid():
    req = InvestigationRequest(
        question="Explain physical surface changes across the specified AOI",
        observation_ids=["obs_1", "obs_2"],
    )
    res = InvestigationPlanner.validate(req)
    assert res.valid is True
    assert len(res.errors) == 0
    assert len(res.planned_specialists) > 0


def test_planner_validation_too_short():
    req = InvestigationRequest(
        question="hi",
        observation_ids=[],
    )
    res = InvestigationPlanner.validate(req)
    assert res.valid is False
    assert any("too short" in e.lower() for e in res.errors)
