"""
Test Suite: Concurrent AI Requests & Cross-Contamination Isolation (Test Group Q, Sections 127-129)
Verifies that simultaneous exploration queries maintain complete isolation with no global state leakage.
"""

import concurrent.futures
from exploration.ai_schemas import (
    ExploreAIQueryRequest,
    ExploreCommandPlan,
    FlyToCommand,
    ExploreIntent,
    ExploreIntentType,
)
from exploration.ai_service import explore_ai_service
from unittest.mock import patch


def _run_mocked_query(city: str, lat: float, lon: float):
    req = ExploreAIQueryRequest(
        query=f"Take me to {city}",
        active_layer_ids=["layer-base-dark"],
    )

    intent_obj = ExploreIntent(
        intent=ExploreIntentType.NAVIGATION,
        confidence=0.99,
        location_query=city,
    )

    plan_obj = ExploreCommandPlan(
        intent="navigation",
        summary=f"Fly to {city}",
        commands=[FlyToCommand(location_query=city, latitude=lat, longitude=lon, zoom=10.0)],
    )

    with patch("llm.model_registry.LocalModelRegistry.is_ollama_online", return_value=True), \
         patch("llm.ollama_provider.OllamaProvider.generate_structured_native", side_effect=[intent_obj, plan_obj]):
        res = explore_ai_service.process_query(req)
        return res


def test_concurrent_queries_no_cross_contamination():
    queries = [
        ("Nagpur", 21.1458, 79.0882),
        ("Mumbai", 19.0760, 72.8777),
        ("New Delhi", 28.6139, 77.2090),
        ("Bengaluru", 12.9716, 77.5946),
    ]

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(_run_mocked_query, city, lat, lon): city
            for city, lat, lon in queries
        }
        for future in concurrent.futures.as_completed(futures):
            city = futures[future]
            results[city] = future.result()

    # Verify all succeeded with unique IDs
    request_ids = set()
    for city, lat, lon in queries:
        res = results[city]
        assert res.status == "completed"
        assert res.request_id not in request_ids
        request_ids.add(res.request_id)

        # Assert camera coordinates match requested city, NOT cross-contaminated
        assert res.state_patch.camera is not None
        assert res.state_patch.camera["latitude"] == lat
        assert res.state_patch.camera["longitude"] == lon
        assert city.lower() in res.summary.lower()
