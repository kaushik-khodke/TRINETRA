"""
Unit tests for Single-Image Analysis (VQA, Scene Captioning, Text-Guided Grounding).
"""

import numpy as np
import pytest
from analysis_engine.single_image.grounding import GroundingSpecialistAdapter
from analysis_engine.single_image.service import SingleImageAnalysisService
from analysis_engine.context import AnalysisContext


def test_grounding_adapter_detections():
    adapter = GroundingSpecialistAdapter()
    arr = np.zeros((128, 128, 3), dtype=np.uint8)
    meta = {"width": 128, "height": 128, "modality": "optical"}

    detections = adapter.locate_features(arr, meta, query="Locate the central water reservoir")
    assert isinstance(detections, list)
    for d in detections:
        assert len(d.bbox) == 4
        assert 0.0 <= d.confidence <= 1.0
        assert d.geometry["type"] == "Polygon"


def test_single_image_service_vqa_routing():
    service = SingleImageAnalysisService()
    ctx = AnalysisContext(
        run_id="run_vqa_test",
        query="Is there cloud cover present in this image?",
        mode="SINGLE_IMAGE",
        tensors={"arr_a": np.zeros((128, 128, 3), dtype=np.float32)},
    )
    pack = service.execute_pipeline(ctx)
    assert pack.mode == "SINGLE_IMAGE"
    assert "statistics" in pack.dict()
