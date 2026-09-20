"""
Unit Tests — Raster Service
Verifies metadata inspection, windowed raster reads, and display normalizations.
"""

import os
import pytest
import numpy as np
from exploration.raster_service import RasterService

SAMPLE_TIF = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "sample_data",
    "explore",
    "sentinel2_nagpur_truecolor.tif",
)


def test_read_metadata_from_geotiff():
    assert os.path.exists(SAMPLE_TIF), f"Fixture not found: {SAMPLE_TIF}"
    source = RasterService.read_metadata(SAMPLE_TIF, "test_nagpur_opt")

    assert source.asset_id == "test_nagpur_opt"
    assert source.width == 256
    assert source.height == 256
    assert source.bands == 4
    assert source.crs == "EPSG:4326"
    assert len(source.bounds) == 4
    assert abs(source.bounds[0] - 79.0) < 0.01
    assert abs(source.bounds[1] - 21.0) < 0.01


def test_read_window_spatial_subset():
    # Request bounds covering central portion [79.05, 21.05, 79.15, 21.15]
    window_bounds = [79.05, 21.05, 79.15, 21.15]
    arr = RasterService.read_window(SAMPLE_TIF, window_bounds, out_shape=(128, 128))

    assert arr is not None
    assert arr.shape[0] == 128
    assert arr.shape[1] == 128
    # Has color bands
    assert arr.ndim == 3


def test_read_window_out_of_bounds_returns_none():
    # Completely disjoint coordinates in Arctic
    disjoint_bounds = [0.0, 80.0, 5.0, 85.0]
    arr = RasterService.read_window(SAMPLE_TIF, disjoint_bounds)
    assert arr is None


def test_display_normalization():
    # Create test raw uint16 or high dynamic range array
    raw = np.array([[100, 2000, 15000], [50, 8000, 3000]], dtype=np.uint16)
    rgb = RasterService.normalize_for_display(raw, modality="optical")

    assert rgb.dtype == np.uint8
    assert rgb.ndim == 3
    assert rgb.shape[-1] == 3
    assert np.min(rgb) >= 0
    assert np.max(rgb) <= 255
