"""
Unit Tests: AOI Simplifier
Verifies adaptive Douglas-Peucker simplification bounds and vertex reduction.
"""

import math
from exploration.aoi.simplifier import AOISimplifier


def test_aoi_simplification_reduces_vertices():
    # Generate high-resolution circle polygon with 120 vertices
    center_lon, center_lat = 79.0, 21.0
    radius = 0.05
    coords = []
    for i in range(120):
        angle = (2 * math.pi * i) / 120
        coords.append([center_lon + radius * math.cos(angle), center_lat + radius * math.sin(angle)])
    coords.append(coords[0])  # Close ring

    complex_geom = {"type": "Polygon", "coordinates": [coords]}
    assert len(coords) == 121

    simplified = AOISimplifier.simplify(complex_geom, max_vertices=30)
    simplified_coords = simplified["coordinates"][0]
    assert len(simplified_coords) <= 30
    assert len(simplified_coords) >= 4
    # First and last must still match
    assert simplified_coords[0] == simplified_coords[-1]
