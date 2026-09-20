"""
Test Suite: Malformed LLM Response Recovery (Test Group C)
Verifies graceful handling of non-JSON text, empty responses, and schema violations.
"""

from unittest.mock import patch
from exploration.ai_schemas import ExploreAIQueryRequest, EXPLORE_LLM_INVALID_OUTPUT
from exploration.ai_service import explore_ai_service


def test_malformed_llm_returns_non_json():
    req = ExploreAIQueryRequest(query="Take me to Nagpur and show Sentinel-2")

    # Mock Ollama online but returning non-JSON garbage string
    with patch("llm.model_registry.LocalModelRegistry.is_ollama_online", return_value=True), \
         patch("llm.ollama_provider.OllamaProvider.generate_structured_native", return_value=None):

        res = explore_ai_service.process_query(req)
        assert res.status == "error"
        assert res.error_code == EXPLORE_LLM_INVALID_OUTPUT
        assert len(res.commands) == 0
        assert "Failed to classify exploration intent" in res.summary


def test_malformed_empty_intent():
    req = ExploreAIQueryRequest(query="Take me to Nagpur and show Sentinel-2")

    with patch("llm.model_registry.LocalModelRegistry.is_ollama_online", return_value=True), \
         patch("llm.ollama_provider.OllamaProvider.generate_structured_native", side_effect=[Exception("Malformed JSON"), None]):

        res = explore_ai_service.process_query(req)
        assert res.status == "error"
        assert len(res.commands) == 0
