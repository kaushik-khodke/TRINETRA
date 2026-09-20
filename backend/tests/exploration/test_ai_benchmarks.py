"""
Performance Benchmark Suite: Explore AI Gateway (Step 21)
Measures Fast-Path latency (p50/p95), AI-Path throughput, prompt token bounds, and LRU cache stability.
Saves authoritative performance baseline to backend/outputs/performance/explore_phase3_ai.json.
"""

import json
import os
import time
from typing import List
import numpy as np
from unittest.mock import patch

from exploration.ai_schemas import (
    ExploreAIQueryRequest,
    ExploreIntent,
    ExploreIntentType,
    ExploreCommandPlan,
    FlyToCommand,
    ShowLayerCommand,
)
from exploration.ai_service import explore_ai_service
from exploration.fallback_parser import FallbackParser
from exploration.geo_resolver import GeoResolver
from exploration.prompts import build_planner_prompt


def test_ai_performance_benchmarks():
    # 1. Fast Path Latency Benchmark
    fast_phrases = ["reset", "zoom in", "zoom out", "show boundaries", "hide boundaries"]
    fast_latencies: List[float] = []

    # Warmup
    for p in fast_phrases:
        FallbackParser.parse(p)

    for _ in range(50):
        for p in fast_phrases:
            t0 = time.perf_counter()
            plan = FallbackParser.parse(p)
            assert plan is not None
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            fast_latencies.append(elapsed_ms)

    fast_p50 = float(np.percentile(fast_latencies, 50))
    fast_p95 = float(np.percentile(fast_latencies, 95))
    fast_max = float(np.max(fast_latencies))

    # Fast path must be strictly sub-millisecond
    assert fast_p50 < 0.5, f"Fast path p50 too slow: {fast_p50:.4f} ms"
    assert fast_p95 < 1.0, f"Fast path p95 too slow: {fast_p95:.4f} ms"

    # 2. AI Path Latency Benchmark (Mocked LLM)
    mock_intent = ExploreIntent(
        intent=ExploreIntentType.COMBINED,
        confidence=0.98,
        location_query="Nagpur",
    )
    mock_plan = ExploreCommandPlan(
        intent="combined",
        summary="Fly to Nagpur and show Sentinel-2",
        commands=[
            FlyToCommand(location_query="Nagpur"),
            ShowLayerCommand(layer_id="layer-local_sentinel2_nagpur_truecolor"),
        ],
    )

    def _mock_gen(*args, **kwargs):
        schema_arg = kwargs.get("schema") or (args[1] if len(args) > 1 else None)
        role_arg = kwargs.get("role") or (args[2] if len(args) > 2 else None)
        if role_arg == "fast_router" or schema_arg == ExploreIntent:
            return mock_intent
        return mock_plan

    ai_latencies: List[float] = []
    with patch("llm.model_registry.LocalModelRegistry.is_ollama_online", return_value=True), \
         patch("llm.ollama_provider.OllamaProvider.generate_structured_native", side_effect=_mock_gen):

        for _ in range(30):
            req = ExploreAIQueryRequest(query="Go to Nagpur and show Sentinel-2")
            t0 = time.perf_counter()
            res = explore_ai_service.process_query(req)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            assert res.status == "completed"
            ai_latencies.append(elapsed_ms)

    ai_p50 = float(np.percentile(ai_latencies, 50))
    ai_p95 = float(np.percentile(ai_latencies, 95))

    # 3. Prompt Context Size Bound Verification
    sample_layers = [
        {"id": f"layer_{i}", "name": f"Satellite Band Layer {i}"}
        for i in range(10)
    ]
    prompt_text = build_planner_prompt(
        query="Go to Nagpur and show Sentinel-2",
        intent=mock_intent,
        available_layers=sample_layers,
        active_layers=["layer-base-dark"],
    )
    prompt_chars = len(prompt_text)
    est_tokens = int(prompt_chars / 4.0)

    # Context must be compact (< 1000 estimated tokens)
    assert est_tokens < 1000, f"Prompt bloat detected: {est_tokens} tokens"

    # 4. Cache Bounds & Repeated Query Stability
    for i in range(300):
        GeoResolver.resolve(f"Location_{i % 50}")
    assert len(GeoResolver._cache) <= GeoResolver._MAX_CACHE_SIZE

    # 5. Record Authoritative Metrics Artifact
    metrics = {
        "phase": 3,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "fast_path": {
            "p50_latency_ms": round(fast_p50, 4),
            "p95_latency_ms": round(fast_p95, 4),
            "max_latency_ms": round(fast_max, 4),
            "target_submillisecond": True,
            "status": "PASS",
        },
        "ai_gateway_mocked": {
            "p50_latency_ms": round(ai_p50, 3),
            "p95_latency_ms": round(ai_p95, 3),
            "sample_count": len(ai_latencies),
            "status": "PASS",
        },
        "prompt_context": {
            "character_count": prompt_chars,
            "estimated_token_count": est_tokens,
            "bounded_under_1000_tokens": True,
            "status": "PASS",
        },
        "geo_cache": {
            "max_configured_size": GeoResolver._MAX_CACHE_SIZE,
            "current_size": len(GeoResolver._cache),
            "unbounded_growth_prevented": True,
            "status": "PASS",
        },
    }

    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "outputs", "performance")
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "explore_phase3_ai.json")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    assert os.path.exists(out_file)
