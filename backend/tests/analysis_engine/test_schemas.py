"""
Unit tests for Analysis Engine Pydantic models, requests, results, and findings schemas.
"""

import pytest
from pydantic import ValidationError
from analysis_engine.schemas import (
    AnalysisMode,
    ConfidenceLevel,
    LimitationCode,
    AnalysisRequest,
    AnalysisResult,
    AnalysisFinding,
    AnalysisLimitation,
)


def test_analysis_mode_enum():
    assert AnalysisMode.BI_TEMPORAL.value == "BI_TEMPORAL"
    assert AnalysisMode.SAR_OPTICAL.value == "SAR_OPTICAL"
    assert AnalysisMode.SINGLE_IMAGE.value == "SINGLE_IMAGE"


def test_analysis_request_valid():
    req = AnalysisRequest(
        query="What changed in this agricultural zone?",
        mode=AnalysisMode.BI_TEMPORAL,
        observation_a_id="obs_01",
        observation_b_id="obs_02",
        aoi={"type": "Polygon", "coordinates": [[[79.0, 21.0], [79.1, 21.0], [79.1, 21.1], [79.0, 21.1], [79.0, 21.0]]]},
    )
    assert req.mode == AnalysisMode.BI_TEMPORAL
    assert req.observation_a_id == "obs_01"


def test_analysis_finding_schema():
    finding = AnalysisFinding(
        id="F01",
        title="Urban Expansion",
        label="Built-up Change",
        statement="New structures detected in north quadrant.",
        confidence=ConfidenceLevel.HIGH,
        evidence_ids=["E_CHG01", "E_CHG02"],
        area_m2=15000.0,
        area_ha=1.5,
    )
    assert finding.id == "F01"
    assert finding.confidence == ConfidenceLevel.HIGH
    assert len(finding.evidence_ids) == 2


def test_analysis_limitation_schema():
    lim = AnalysisLimitation(
        code=LimitationCode.CLOUD_CONTAMINATION,
        description="Southwest boundary has partial cirrus cloud presence.",
        severity="warning",
    )
    assert lim.code == LimitationCode.CLOUD_CONTAMINATION
