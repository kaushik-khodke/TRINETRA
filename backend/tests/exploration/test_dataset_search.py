"""
Test Suite: Dataset Search Delegation & ID Safety (Test Groups T & U)
Verifies that AI routes dataset requests through DataBroker without fabricating dataset IDs.
"""

from unittest.mock import patch
from exploration.ai_schemas import (
    ExploreAIQueryRequest,
    ExploreIntent,
    ExploreIntentType,
    ExploreCommandPlan,
    SearchDatasetsCommand,
    AddDatasetLayerCommand,
    EXPLORE_DATASET_NOT_FOUND,
)
from exploration.ai_service import explore_ai_service
from exploration.command_validator import CommandValidator


def test_dataset_search_intent_delegation():
    req = ExploreAIQueryRequest(query="Find Sentinel-2 imagery over Nagpur")

    intent_obj = ExploreIntent(
        intent=ExploreIntentType.DATASET_SEARCH,
        confidence=0.95,
        location_query="Nagpur",
        dataset_query="Sentinel-2",
    )

    plan_obj = ExploreCommandPlan(
        intent="dataset_search",
        summary="Search Sentinel-2 imagery over Nagpur",
        commands=[
            SearchDatasetsCommand(
                query="Sentinel-2",
                location_query="Nagpur",
                collection="sentinel-2-l2a",
                max_results=10,
            )
        ],
    )

    with patch("llm.model_registry.LocalModelRegistry.is_ollama_online", return_value=True), \
         patch("llm.ollama_provider.OllamaProvider.generate_structured_native", side_effect=[intent_obj, plan_obj]):
        res = explore_ai_service.process_query(req)
        assert res.status == "completed"
        assert res.intent == "dataset_search"
        assert len(res.commands) == 1
        assert res.commands[0].type == "SEARCH_DATASETS"
        assert "sentinel-2" in res.commands[0].message.lower()


def test_reject_fabricated_dataset_id():
    # Attempting to add a layer using an invented/hallucinated dataset ID
    cmd = AddDatasetLayerCommand(asset_id="fake_hallucinated_item_9999")
    is_valid, err_code, err_msg = CommandValidator.validate_command(cmd)
    assert is_valid is False
    assert err_code == EXPLORE_DATASET_NOT_FOUND
    assert "not found" in err_msg
