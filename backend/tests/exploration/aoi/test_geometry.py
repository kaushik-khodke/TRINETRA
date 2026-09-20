"""
Unit Tests: AOI Geometry Utilities & Deterministic Hashing
Verifies bbox, centroid, area calculation, coordinate normalization, and invariant hashing.
"""

from exploration.aoi.geometry import (
    get_bbox,
    calculate_centroid,
    calculate_area_km2,
    normalize_longitudes,
    geometry_hash,
)


def test_geometry_bbox_and_centroid():
    geom = {
        "type": "Polygon",
        "coordinates": [
            [
                [79.0, 21.0],
                [80.0, 21.0],
                [80.0, 22.0],
                [79.0, 22.0],
                [79.0, 21.0],
            ]
        ],
    }
    bbox = get_bbox(geom)
    assert bbox == [79.0, 21.0, 80.0, 22.0]

    centroid = calculate_centroid(geom)
    assert abs(centroid["latitude"] - 21.5) < 0.01
    assert abs(centroid["longitude"] - 79.5) < 0.01


def test_geometry_area_calculation():
    geom = {
        "type": "Polygon",
        "coordinates": [
            [
                [79.0, 21.0],
                [79.1, 21.0],
                [79.1, 21.1],
                [79.0, 21.1],
                [79.0, 21.0],
            ]
        ],
    }
    area = calculate_area_km2(geom)
    # Approx 10km x 11km = ~110 - 125 km2
    assert 90.0 < area < 150.0


def test_deterministic_geometry_hashing():
    geom1 = {
        "type": "Polygon",
        "coordinates": [[[79.0, 21.0], [79.1, 21.0], [79.1, 21.1], [79.0, 21.1], [79.0, 21.0]]],
    }
    geom2 = {
        "coordinates": [[[79.0000001, 21.0], [79.1, 21.0], [79.1, 21.1], [79.0, 21.1], [79.0, 21.0]]],
        "type": "Polygon",
    }
    # Rounding to 6 decimal places should make these hashes match!
    h1 = geometry_hash(geom1)
    h2 = geometry_hash(geom2)
    assert h1 == h2
    assert len(h1) == 16


def test_normalize_longitudes():
    geom_out = {
        "type": "Polygon",
        "coordinates": [[[190.0, 21.0], [191.0, 21.0], [191.0, 22.0], [190.0, 22.0], [190.0, 21.0]]],
    }
    norm = normalize_longitudes(geom_out)
    for ring in norm["coordinates"]:
        for pt in ring:
            assert -180.0 <= pt[0] <= 180.0
