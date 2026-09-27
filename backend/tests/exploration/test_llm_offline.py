"""
Test Suite: LLM Offline Resiliency & Timeout Handling (Test Groups S & R)
Verifies that the workstation remains functional when Ollama is offline or experiences socket timeout.
"""

import socket
from unittest.mock import patch
from exploration.ai_schemas import ExploreAIQueryRequest
from exploration.ai_service import explore_ai_service


def test_llm_offline_fallback_commands_succeed():
    # Simple deterministic commands MUST work even if Ollama is totally offline
    with patch("llm.model_registry.LocalModelRegistry.is_ollama_online", return_value=False):
        req_reset = ExploreAIQueryRequest(query="reset", active_layer_ids=["layer-base-dark"])
        res_reset = explore_ai_service.process_query(req_reset)
        assert res_reset.status == "completed"
        assert res_reset.fast_path is True
        assert res_reset.state_patch.camera is not None

        req_borders = ExploreAIQueryRequest(query="show boundaries", active_layer_ids=["layer-base-dark"])
        res_borders = explore_ai_service.process_query(req_borders)
        assert res_borders.status == "completed"
        assert res_borders.fast_path is True
        assert "layer-borders" in res_borders.state_patch.visible_layer_ids


def test_llm_offline_complex_query_handled_gracefully():
    # Complex query that cannot be parsed deterministically returns a polite offline notification
    with patch("llm.model_registry.LocalModelRegistry.is_ollama_online", return_value=False):
        req = ExploreAIQueryRequest(query="Find Sentinel-2 observations over Nagpur with low cloud cover")
        res = explore_ai_service.process_query(req)
        assert res.status == "rejected"
        assert res.error_code == "EXPLORE_PROVIDER_UNAVAILABLE"
        assert "Local Ollama service is offline" in res.summary
        assert len(res.commands) == 0


def test_llm_socket_timeout_handled_gracefully():
    with patch("llm.model_registry.LocalModelRegistry.is_ollama_online", return_value=True), \
         patch("llm.ollama_provider.OllamaProvider.generate_structured_native", side_effect=socket.timeout("Socket timeout")):
        req = ExploreAIQueryRequest(query="Take me to Nagpur and show Sentinel-2")
        res = explore_ai_service.process_query(req)
        assert res.status == "error"
        assert len(res.commands) == 0
