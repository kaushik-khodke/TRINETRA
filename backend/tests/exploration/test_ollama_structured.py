"""
Test Suite: Native Ollama Structured Output Generation (Test Group B)
Verifies schema injection, format parameter payload, and Pydantic model validation with mocked Ollama.
"""

import json
from unittest.mock import patch, MagicMock
from exploration.ai_schemas import ExploreCommandPlan, FlyToCommand, ShowLayerCommand
from llm.ollama_provider import OllamaProvider


def test_generate_structured_native_success():
    expected_plan = {
        "intent": "combined",
        "summary": "Navigate to Nagpur and display Sentinel-2",
        "commands": [
            {
                "type": "FLY_TO",
                "location_query": "Nagpur",
                "latitude": 21.1458,
                "longitude": 79.0882,
                "zoom": 10.0,
                "heading": 0.0,
                "pitch": 0.0,
                "duration": 1.5,
            },
            {
                "type": "SHOW_LAYER",
                "layer_id": "layer-local_sentinel2_nagpur_truecolor",
            },
        ],
    }

    mock_resp_data = {
        "response": json.dumps(expected_plan),
        "prompt_eval_count": 45,
        "eval_count": 38,
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(mock_resp_data).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("llm.model_registry.LocalModelRegistry.is_ollama_online", return_value=True), \
         patch("llm.model_registry.LocalModelRegistry.resolve_model_for_role", return_value=("qwen2.5:7b", True)), \
         patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:

        result = OllamaProvider.generate_structured_native(
            prompt="Go to Nagpur and show Sentinel-2",
            schema=ExploreCommandPlan,
            role="planner",
        )

        assert result is not None
        assert isinstance(result, ExploreCommandPlan)
        assert result.intent == "combined"
        assert len(result.commands) == 2
        assert result.commands[0].type == "FLY_TO"
        assert result.commands[0].location_query == "Nagpur"
        assert result.commands[1].type == "SHOW_LAYER"

        # Verify outgoing request payload format
        args, kwargs = mock_urlopen.call_args
        req = args[0]
        payload = json.loads(req.data.decode("utf-8"))
        assert payload["model"] == "qwen2.5:7b"
        assert payload["stream"] is False
        assert payload["options"]["temperature"] == 0.0
        assert "format" in payload
        assert payload["format"]["type"] == "object"
