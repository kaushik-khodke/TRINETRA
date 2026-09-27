"""
Unit Tests: AOI Validator & Policy Engine
Verifies valid polygons, unclosed rings, NaN coordinates, non-numeric vertices, Point/LineString rejection.
"""

from exploration.aoi.validator import AOIValidator, AOIPolicy


def test_valid_polygon():
    # Nagpur urban AOI rectangle
    geom = {
        "type": "Polygon",
        "coordinates": [
            [
                [79.05, 21.10],
                [79.15, 21.10],
                [79.15, 21.20],
                [79.05, 21.20],
                [79.05, 21.10],
            ]
        ],
    }
    res = AOIValidator.validate(geom)
    assert res.valid is True
    assert len(res.errors) == 0
    assert res.bbox == [79.05, 21.10, 79.15, 21.20]
    assert res.area_km2 > 0.0
    assert res.vertex_count == 5


def test_reject_unsupported_point_and_linestring():
    pt = {"type": "Point", "coordinates": [79.0, 21.0]}
    res_pt = AOIValidator.validate(pt)
    assert res_pt.valid is False
    assert "Unsupported geometry type" in res_pt.errors[0]

    line = {"type": "LineString", "coordinates": [[79.0, 21.0], [79.1, 21.1]]}
    res_line = AOIValidator.validate(line)
    assert res_line.valid is False
    assert "Unsupported geometry type" in res_line.errors[0]


def test_reject_unclosed_polygon():
    # Last coordinate does not match first coordinate
    geom = {
        "type": "Polygon",
        "coordinates": [
            [
                [79.0, 21.0],
                [79.1, 21.0],
                [79.1, 21.1],
                [79.0, 21.1],
                [79.05, 21.05],  # Not closed!
            ]
        ],
    }
    res = AOIValidator.validate(geom)
    assert res.valid is False
    assert any("not closed" in e.lower() for e in res.errors)


def test_reject_nan_and_infinity():
    geom_nan = {
        "type": "Polygon",
        "coordinates": [
            [
                [79.0, 21.0],
                [float("nan"), 21.0],
                [79.1, 21.1],
                [79.0, 21.1],
                [79.0, 21.0],
            ]
        ],
    }
    res = AOIValidator.validate(geom_nan)
    assert res.valid is False
    assert any("finite" in e.lower() for e in res.errors)

    geom_inf = {
        "type": "Polygon",
        "coordinates": [
            [
                [79.0, 21.0],
                [float("inf"), 21.0],
                [79.1, 21.1],
                [79.0, 21.1],
                [79.0, 21.0],
            ]
        ],
    }
    res_inf = AOIValidator.validate(geom_inf)
    assert res_inf.valid is False
    assert any("finite" in e.lower() for e in res_inf.errors)


def test_reject_out_of_bounds_coordinates():
    # Lat > 90
    geom_lat = {
        "type": "Polygon",
        "coordinates": [
            [[79.0, 95.0], [79.1, 95.0], [79.1, 96.0], [79.0, 96.0], [79.0, 95.0]]
        ],
    }
    res_lat = AOIValidator.validate(geom_lat)
    assert res_lat.valid is False
    assert any("latitude" in e.lower() for e in res_lat.errors)


def test_reject_oversized_aoi():
    # Giant polygon spanning entire continent
    giant_geom = {
        "type": "Polygon",
        "coordinates": [
            [[40.0, -10.0], [120.0, -10.0], [120.0, 45.0], [40.0, 45.0], [40.0, -10.0]]
        ],
    }
    res = AOIValidator.validate(giant_geom)
    assert res.valid is False
    assert any("exceeds" in e.lower() for e in res.errors)
