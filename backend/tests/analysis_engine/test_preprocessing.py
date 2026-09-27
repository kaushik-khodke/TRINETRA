"""
Unit tests for Windowed Raster Preprocessing, Tile Planner, Alignment, and Quality Masking.
"""

import os
import numpy as np
import pytest
from analysis_engine.preprocessing.raster import RasterPreprocessor
from analysis_engine.preprocessing.alignment import RasterGridAligner
from analysis_engine.preprocessing.normalization import RadiometricNormalizer
from analysis_engine.preprocessing.masking import QualityMaskManager
from analysis_engine.preprocessing.reprojection import CoordinateReprojector


FIXTURE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fixtures", "explore_analysis")
OPTICAL_A = os.path.join(FIXTURE_DIR, "optical_a.tif")
SAR_A = os.path.join(FIXTURE_DIR, "sar_a.tif")
NODATA_SCENE = os.path.join(FIXTURE_DIR, "nodata_scene.tif")


def test_windowed_read_small_aoi():
    """Verifies that reading a windowed sub-area returns a valid spatial array without full loading."""
    bounds = [79.02, 21.02, 79.08, 21.08]
    arr, meta = RasterPreprocessor.read_window_array(OPTICAL_A, bounds, (64, 64))
    assert arr is not None
    assert arr.shape == (64, 64, 3)
    assert meta["width"] == 64
    assert meta["height"] == 64


def test_tile_planning_and_stitching():
    """Verifies overlapping tile division and seamless tile recombination."""
    H, W = 1000, 1000
    tile_size = 512
    overlap = 64

    tiles = RasterPreprocessor.plan_tiles(height=H, width=W, tile_size=tile_size, overlap=overlap)
    assert len(tiles) >= 4

    # Mock predictions
    tiles_data = []
    for t in tiles:
        sub = np.ones((t["height"], t["width"]), dtype=np.float32)
        tiles_data.append((t, sub))

    stitched = RasterPreprocessor.stitch_tiles(tiles_data, (H, W))
    assert stitched.shape == (H, W)
    # Uniform 1.0 everywhere
    np.testing.assert_allclose(stitched, 1.0, rtol=1e-4)


def test_raster_grid_aligner():
    """Verifies resampling to a common grid."""
    arr_a = np.ones((100, 100, 3), dtype=np.float32)
    arr_b = np.ones((200, 200, 3), dtype=np.float32)

    aligned_a, aligned_b, report = RasterGridAligner.align_pair(
        arr_a=arr_a,
        meta_a={"crs": "EPSG:4326"},
        arr_b=arr_b,
        meta_b={"crs": "EPSG:4326"},
        reference="a",
    )
    assert aligned_a.shape == (100, 100, 3)
    assert aligned_b.shape == (100, 100, 3)
    assert report["resampled"] is True


def test_radiometric_normalizer():
    # Optical scaling
    opt = np.array([0, 5000, 10000], dtype=np.float32)
    norm_opt, meta = RadiometricNormalizer.normalize_optical(opt, {})
    assert norm_opt[0] == 0.0
    assert norm_opt[1] == 0.5
    assert norm_opt[2] == 1.0

    # SAR Decibel conversion
    sar_linear = np.array([0.001, 0.1, 10.0], dtype=np.float32)
    sar_db, sar_meta = RadiometricNormalizer.normalize_sar(sar_linear, {}, convert_to_db=True)
    assert sar_meta["converted_to_db"] is True
    assert sar_db[0] <= -20.0


def test_quality_mask_and_suppression():
    """Verifies that changes over nodata/invalid pixels are suppressed."""
    arr = np.ones((50, 50), dtype=np.float32)
    arr[0:10, :] = np.nan  # Invalid top 10 rows

    valid_mask = QualityMaskManager.build_validity_mask(arr)
    assert np.all(valid_mask[0:10, :] == False)
    assert np.all(valid_mask[10:, :] == True)

    # Change detected everywhere
    change_mask = np.ones((50, 50), dtype=bool)
    clean_change, contamination = QualityMaskManager.filter_evidence_by_mask(change_mask, valid_mask)
    assert np.all(clean_change[0:10, :] == False)
    assert contamination == pytest.approx(0.20, abs=0.01)


def test_coordinate_reprojector():
    # EPSG:4326 to EPSG:3857
    x, y = CoordinateReprojector.reproject_point(79.0, 21.0, "EPSG:4326", "EPSG:3857")
    assert x > 8_000_000  # meters
    assert y > 2_000_000
