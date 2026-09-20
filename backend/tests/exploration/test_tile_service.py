"""
Unit Tests — Tile Service
Verifies slippy tile coordinate calculations, windowed tile generation, and PNG encoding.
"""

import io
import os
import pytest
from PIL import Image
from exploration.tile_service import TileService
from exploration.raster_service import RasterService

SAMPLE_TIF = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "sample_data",
    "explore",
    "sentinel2_nagpur_truecolor.tif",
)


def test_tile_coordinate_validation():
    # Valid
    valid, _ = TileService.validate_tile_coords(10, 500, 500)
    assert valid is True

    # Invalid zoom
    valid, err = TileService.validate_tile_coords(25, 0, 0)
    assert valid is False
    assert "Invalid zoom" in err

    # Out of bounds X for zoom 2 (max is 3)
    valid, err = TileService.validate_tile_coords(2, 5, 1)
    assert valid is False
    assert "Invalid x coordinate" in err


def test_tile_to_wgs84_bounds():
    # Zoom 0 tile (0, 0) covers entire globe
    bounds = TileService.tile_to_wgs84_bounds(0, 0, 0)
    assert abs(bounds[0] - (-180.0)) < 1e-4
    assert abs(bounds[2] - 180.0) < 1e-4
    assert abs(bounds[1] - (-85.05)) < 1.0
    assert abs(bounds[3] - 85.05) < 1.0


def test_tile_generation_returns_valid_png():
    source = RasterService.read_metadata(SAMPLE_TIF, "tile_test_source")

    # Tile for central India around Nagpur (lat ~21.1, lon ~79.1) at zoom 8
    # lon 79.1 -> x = int((79.1 + 180) / 360 * 256) = 184
    # lat 21.1 -> y = 112
    tile_bytes = TileService.get_tile("layer-test", source, z=8, x=184, y=112)

    assert tile_bytes is not None
    assert len(tile_bytes) > 100

    # Verify PNG image format & size
    img = Image.open(io.BytesIO(tile_bytes))
    assert img.format == "PNG"
    assert img.size == (256, 256)


def test_tile_generation_disjoint_returns_none():
    source = RasterService.read_metadata(SAMPLE_TIF, "tile_test_source")
    # Tile in Pacific Ocean (z=8, x=10, y=10)
    tile_bytes = TileService.get_tile("layer-test", source, z=8, x=10, y=10)
    assert tile_bytes is None
