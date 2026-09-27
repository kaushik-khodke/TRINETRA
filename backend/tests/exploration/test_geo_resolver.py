"""
Test Suite: GeoResolver & Coordinate Parsing (Test Groups I, J, K)
Verifies coordinate parser, offline gazetteer, ambiguity detection, and LRU cache.
"""

from exploration.geo_resolver import GeoResolver, DeterministicCoordinateParser


def test_deterministic_coordinate_parser():
    # Comma separated
    target1 = DeterministicCoordinateParser.parse("21.1458, 79.0882")
    assert target1 is not None
    assert target1.latitude == 21.1458
    assert target1.longitude == 79.0882
    assert target1.source == "coordinate_parser"

    # With spaces
    target2 = DeterministicCoordinateParser.parse("  21.1458 ,  79.0882  ")
    assert target2 is not None
    assert target2.latitude == 21.1458

    # Keyword format
    target3 = DeterministicCoordinateParser.parse("lat 21.1458 lon 79.0882")
    assert target3 is not None
    assert target3.latitude == 21.1458
    assert target3.longitude == 79.0882


def test_coordinate_parser_rejects_out_of_bounds():
    # Lat > 90
    assert DeterministicCoordinateParser.parse("100.0, 79.0") is None
    # Lat < -90
    assert DeterministicCoordinateParser.parse("-95.0, 79.0") is None
    # Lon > 180
    assert DeterministicCoordinateParser.parse("20.0, 200.0") is None
    # Lon < -180
    assert DeterministicCoordinateParser.parse("20.0, -195.0") is None


def test_geo_resolver_gazetteer():
    target = GeoResolver.resolve("Nagpur")
    assert target is not None
    assert "Nagpur" in target.name
    assert target.latitude == 21.1458
    assert target.longitude == 79.0882
    assert target.is_ambiguous is False
    assert target.bbox is not None

    target_mumbai = GeoResolver.resolve("mumbai")
    assert target_mumbai is not None
    assert target_mumbai.latitude == 19.0760

    target_delhi = GeoResolver.resolve("New Delhi")
    assert target_delhi is not None
    assert target_delhi.latitude == 28.6139


def test_geo_resolver_ambiguity_handling():
    # Springfield has multiple candidates and must be flagged as ambiguous
    target = GeoResolver.resolve("Springfield")
    assert target is not None
    assert target.is_ambiguous is True
    assert len(target.candidates) >= 2


def test_geo_resolver_unknown_location():
    target = GeoResolver.resolve("totally_fake_location_xyz_999")
    assert target is None


def test_geo_resolver_caching():
    # Prime cache
    target1 = GeoResolver.resolve("Nagpur")
    assert "nagpur" in GeoResolver._cache
    target2 = GeoResolver.resolve("Nagpur")
    assert target1 is target2
