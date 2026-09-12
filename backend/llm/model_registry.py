"""
SatQuery AI — Local Model Registry
Centralized registry for local Ollama models with dynamic tag discovery,
role mappings, and hardware-aware fallback.
"""

import os
import json
import urllib.request
from typing import Dict, Any, List, Optional, Tuple
from llm.schemas import ModelSpec, ModelRole

class LocalModelRegistry:
    DEFAULT_OLLAMA_HOST = "http://localhost:11434"

    # Default configured model roles
    MODEL_DEFINITIONS: Dict[ModelRole, Dict[str, Any]] = {
        "planner": {
            "default_model": os.environ.get("SATQUERY_PLANNER_MODEL", "qwen3.5:4b"),
            "description": "Primary local reasoning, multi-step planning, and cross-modal synthesis model",
            "context_window": 8192,
            "temperature": 0.2
        },
        "fast_router": {
            "default_model": os.environ.get("SATQUERY_ROUTER_MODEL", "qwen3.5:4b"),
            "description": "High-throughput local model for intent classification and parameter extraction",
            "context_window": 4096,
            "temperature": 0.1
        },
        "lightweight": {
            "default_model": os.environ.get("SATQUERY_LIGHT_MODEL", "llama3.2"),
            "description": "Secondary local model for lightweight summaries and verification",
            "context_window": 4096,
            "temperature": 0.2
        }
    }

    @classmethod
    def get_ollama_host(cls) -> str:
        return os.environ.get("OLLAMA_HOST", cls.DEFAULT_OLLAMA_HOST).rstrip("/")

    @classmethod
    def probe_installed_models(cls) -> List[str]:
        """Queries local Ollama daemon to return list of currently downloaded model tags."""
        url = f"{cls.get_ollama_host()}/api/tags"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SatQuery-AI/LocalRegistry"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", []) if "name" in m]
                return models
        except Exception:
            return []

    @classmethod
    def is_ollama_online(cls) -> bool:
        """Checks whether local Ollama server is reachable."""
        url = f"{cls.get_ollama_host()}/api/tags"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SatQuery-AI/LocalRegistry"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    @classmethod
    def resolve_model_for_role(cls, role: ModelRole) -> Tuple[str, bool]:
        """
        Resolves the actual model tag to use for a given role.
        Returns: (model_tag, is_exact_match_available)
        If the configured model is not installed, falls back to best available installed model.
        """
        spec = cls.MODEL_DEFINITIONS.get(role, cls.MODEL_DEFINITIONS["fast_router"])
        preferred = spec["default_model"]
        installed = cls.probe_installed_models()

        if not installed:
            # No models installed yet, return preferred tag for user guidance
            return preferred, False

        # 1. Exact match
        if preferred in installed:
            return preferred, True

        # 2. Tag match without ':latest' or with ':latest'
        pref_base = preferred.split(":")[0]
        for m in installed:
            if m.startswith(pref_base):
                return m, True

        # 3. Role-based fallback across installed models
        if role == "planner":
            for m in installed:
                if any(k in m.lower() for k in ["qwen3.5:9b", "qwen2.5:7b", "qwen2.5:14b", "mistral:7b"]):
                    return m, True
        elif role == "fast_router":
            for m in installed:
                if any(k in m.lower() for k in ["qwen3.5:4b", "qwen2.5:3b", "qwen2.5:1.5b", "qwen2.5:0.5b", "phi3:mini", "llama3.2:3b", "llama3.2:1b"]):
                    return m, True
        elif role == "lightweight":
            for m in installed:
                if any(k in m.lower() for k in ["llama3.2", "llama3:8b"]):
                    return m, True

        # 4. If no specific compatible model is installed, return configured model and False
        return preferred, False

    @classmethod
    def get_all_specs(cls) -> Dict[str, ModelSpec]:
        """Returns the full registry status with availability indicators."""
        installed = cls.probe_installed_models()
        specs = {}
        for role, defn in cls.MODEL_DEFINITIONS.items():
            active_tag, available = cls.resolve_model_for_role(role)
            specs[role] = ModelSpec(
                role=role,
                default_model=defn["default_model"],
                description=defn["description"],
                context_window=defn["context_window"],
                temperature=defn["temperature"],
                active_model=active_tag,
                is_available=available and (active_tag in installed)
            )
        return specs

    @classmethod
    def get_active_model(cls) -> Optional[ModelSpec]:
        """Returns the primary active planner model spec."""
        specs = cls.get_all_specs()
        planner_spec = specs.get("planner")
        if planner_spec and planner_spec.is_available:
            return planner_spec
        for s in specs.values():
            if s.is_available:
                return s
        return planner_spec

    @classmethod
    def get_status_summary(cls) -> Dict[str, Any]:
        """Holistic summary of local LLM infrastructure for /api/v1/llm-status."""
        online = cls.is_ollama_online()
        installed = cls.probe_installed_models()
        specs = cls.get_all_specs()

        return {
            "ollama_connected": online,
            "ollama_host": cls.get_ollama_host(),
            "installed_models": installed,
            "model_count": len(installed),
            "cloud_llm": False,  # Strict local requirement
            "roles": {
                role: {
                    "configured": spec.default_model,
                    "active": spec.active_model,
                    "available": spec.is_available,
                    "description": spec.description
                }
                for role, spec in specs.items()
            }
        }

# Module-level convenience singleton / alias
local_registry = LocalModelRegistry
