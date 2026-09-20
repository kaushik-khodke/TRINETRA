"""
Unit tests for Evidence Governance and Consistency Validation Gates.
"""

import pytest
from analysis_engine.evidence.validator import EvidenceValidator
from analysis_engine.evidence.models import EvidencePack, ChangeRegionEvidence, GroundingEvidence
from analysis_engine.errors import ReasoningFailureError


def test_validator_rejects_impossible_pixel_math():
    """changed_pixels cannot exceed total_valid_pixels."""
    pack = EvidencePack(
        pack_id="pack_err_1",
        run_id="run_err_1",
        mode="BI_TEMPORAL",
        statistics={
            "changed_pixels": 5000,
            "total_valid_pixels": 1000,  # Impossible!
        },
    )
    with pytest.raises(ReasoningFailureError, match="exceeds total_valid_pixels"):
        EvidenceValidator.validate_pack(pack)


def test_validator_rejects_area_pixel_inconsistency():
    """Area in m² must match changed_pixels * pixel_size_m² within tolerance."""
    pack = EvidencePack(
        pack_id="pack_err_2",
        run_id="run_err_2",
        mode="BI_TEMPORAL",
        statistics={
            "changed_pixels": 100,
            "total_valid_pixels": 1000,
            "pixel_size_meters": 10.0,  # 100 m² per pixel -> expected 10,000 m²
            "area_m2": 50000.0,         # Inconsistent 50,000 m²!
        },
    )
    with pytest.raises(ReasoningFailureError, match="disagrees with pixel count computation"):
        EvidenceValidator.validate_pack(pack)


def test_validator_rejects_malformed_grounding_bbox():
    """Inverted coordinates [ymin > ymax or xmin > xmax] must be rejected."""
    bad_detection = GroundingEvidence(
        id="E_GRD_BAD",
        label="Inverted Box",
        bbox=[0.8, 0.2, 0.1, 0.9],  # ymin=0.8 > ymax=0.1
        confidence=0.85,
    )
    with pytest.raises(ReasoningFailureError, match="inverted coords"):
        EvidenceValidator.validate_grounding(bad_detection)


def test_validator_rejects_negative_area():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ChangeRegionEvidence(
            id="E_CHG_BAD",
            label="Negative Area",
            area_m2=-500.0,
            area_ha=-0.05,
            pixel_count=10,
            centroid=[79.0, 21.0],
            bbox=[79.0, 21.0, 79.1, 21.1],
            geometry={"type": "Polygon", "coordinates": [[[79.0, 21.0], [79.1, 21.0], [79.1, 21.1], [79.0, 21.1], [79.0, 21.0]]]},
            confidence=0.85,
        )

