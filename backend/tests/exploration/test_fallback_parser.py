"""
Test Suite: Deterministic Fallback Parser (Test Group L & M)
Verifies sub-millisecond keyword parsing, alias resolution, and fast-path routing.
"""

import time
from exploration.fallback_parser import FallbackParser


def test_fallback_parser_reset():
    for phrase in ["reset", "reset globe", "RESET", "reset view", "home"]:
        plan = FallbackParser.parse(phrase)
        assert plan is not None, f"Failed for {phrase}"
        assert plan.intent == "reset"
        assert len(plan.commands) == 1
        assert plan.commands[0].type == "RESET_VIEW"


def test_fallback_parser_zoom():
    plan_in = FallbackParser.parse("zoom in")
    assert plan_in is not None
    assert plan_in.commands[0].type == "ZOOM_IN"

    plan_out = FallbackParser.parse("zoom out")
    assert plan_out is not None
    assert plan_out.commands[0].type == "ZOOM_OUT"


def test_fallback_parser_layers():
    plan_show = FallbackParser.parse("show boundaries")
    assert plan_show is not None
    assert plan_show.commands[0].type == "SHOW_LAYER"
    assert plan_show.commands[0].layer_id == "layer-borders"

    plan_hide = FallbackParser.parse("hide boundaries")
    assert plan_hide is not None
    assert plan_hide.commands[0].type == "HIDE_LAYER"
    assert plan_hide.commands[0].layer_id == "layer-borders"


def test_fallback_parser_satellite_aliases():
    plan_s2 = FallbackParser.parse("turn on s2")
    assert plan_s2 is not None
    assert plan_s2.commands[0].layer_id == "layer-local_sentinel2_nagpur_truecolor"

    plan_sar = FallbackParser.parse("show radar")
    assert plan_sar is not None
    assert plan_sar.commands[0].layer_id == "layer-local_sentinel1_mumbai_sar"


def test_fallback_parser_returns_none_for_complex_queries():
    # Complex multi-clause queries or geographic navigation must route to the AI path
    complex_queries = [
        "Take me to Nagpur and show Sentinel-2",
        "Find satellite imagery over Mumbai",
        "Make Sentinel-2 50% transparent",
        "Where is the lake near Nagpur?",
    ]
    for q in complex_queries:
        assert FallbackParser.parse(q) is None


def test_fallback_parser_submillisecond_latency():
    t0 = time.perf_counter()
    for _ in range(100):
        FallbackParser.parse("show boundaries")
    elapsed_ms = ((time.perf_counter() - t0) / 100) * 1000.0
    # Must be faster than 0.5 ms per invocation
    assert elapsed_ms < 0.5, f"Fallback parser was slow: {elapsed_ms:.4f} ms"
