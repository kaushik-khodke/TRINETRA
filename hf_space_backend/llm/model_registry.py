"""
SatQuery AI — Universal Local Model Registry
Auto-detects and connects to WHATEVER model is currently running or installed in local Ollama.
Zero vendor lock-in: seamlessly works with Qwen, Gemma, Llama, Mistral, DeepSeek, Phi,
or any custom model tag without requiring hardcoded model names.
"""

import os
import json
import time
import urllib.request
from typing import Dict, Any, List, Optional, Tuple
from llm.schemas import ModelSpec, ModelRole

class LocalModelRegistry:
    DEFAULT_OLLAMA_HOST = "http://localhost:11434"

    # Fast probe cache to eliminate repetitive socket timeouts when Ollama is offline
    _cache_time: float = 0.0
    _cached_running: List[str] = []
    _cached_installed: List[str] = []
    _cached_online: bool = False

    # Default configured role metadata
    MODEL_DEFINITIONS: Dict[ModelRole, Dict[str, Any]] = {
        "planner": {
            "default_model": os.environ.get("SATQUERY_PLANNER_MODEL") or os.environ.get("OLLAMA_MODEL") or "auto",
            "description": "Primary local reasoning, multi-step planning, and cross-modal synthesis model",
            "context_window": 8192,
            "temperature": 0.2
        },
        "fast_router": {
            "default_model": os.environ.get("SATQUERY_ROUTER_MODEL") or os.environ.get("OLLAMA_MODEL") or "auto",
            "description": "High-throughput local model for intent classification and parameter extraction",
            "context_window": 4096,
            "temperature": 0.1
        },
        "lightweight": {
            "default_model": os.environ.get("SATQUERY_LIGHT_MODEL") or os.environ.get("OLLAMA_MODEL") or "auto",
            "description": "Secondary local model for lightweight summaries and verification",
            "context_window": 4096,
            "temperature": 0.2
        }
    }

    @classmethod
    def get_ollama_host(cls) -> str:
        return os.environ.get("OLLAMA_HOST", cls.DEFAULT_OLLAMA_HOST).rstrip("/")

    @classmethod
    def _refresh_cache(cls, force: bool = False):
        now = time.time()
        if not force and (now - cls._cache_time < 3.0):
            return

        cls._cache_time = now
        host = cls.get_ollama_host()

        # 1. Quick probe /api/tags
        try:
            req = urllib.request.Request(f"{host}/api/tags", headers={"User-Agent": "SatQuery-AI/LocalRegistry"})
            with urllib.request.urlopen(req, timeout=0.6) as resp:
                cls._cached_online = (resp.status == 200)
                data = json.loads(resp.read().decode("utf-8"))
                cls._cached_installed = [m.get("name", "") for m in data.get("models", []) if "name" in m]
        except Exception:
            cls._cached_online = False
            cls._cached_installed = []
            cls._cached_running = []
            return

        # 2. Probe running models /api/ps if online
        try:
            req = urllib.request.Request(f"{host}/api/ps", headers={"User-Agent": "SatQuery-AI/LocalRegistry"})
            with urllib.request.urlopen(req, timeout=0.6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                cls._cached_running = [m.get("name", "") for m in data.get("models", []) if "name" in m]
        except Exception:
            cls._cached_running = []

    @classmethod
    def is_ollama_online(cls) -> bool:
        cls._refresh_cache()
        return cls._cached_online

    @classmethod
    def probe_running_models(cls) -> List[str]:
        cls._refresh_cache()
        return list(cls._cached_running)

    @classmethod
    def probe_installed_models(cls) -> List[str]:
        cls._refresh_cache()
        return list(cls._cached_installed)

    @classmethod
    def resolve_model_for_role(
        cls,
        role: ModelRole,
        running_models: Optional[List[str]] = None,
        installed_models: Optional[List[str]] = None
    ) -> Tuple[str, bool]:
        """
        Dynamically auto-detects and resolves the model tag to use for a given role:
        1. Explicit environment variable (OLLAMA_MODEL or role-specific) if set.
        2. Currently running model in memory (from /api/ps).
        3. Best matching installed model (from /api/tags).
        4. Any installed model available in Ollama (works with ANY LLM developer has).
        5. If Ollama is offline or empty, returns 'auto' and False (triggers local physics engine).
        """
        explicit_env = os.environ.get("OLLAMA_MODEL")
        if role == "planner" and os.environ.get("SATQUERY_PLANNER_MODEL"):
            explicit_env = os.environ.get("SATQUERY_PLANNER_MODEL")
        elif role == "fast_router" and os.environ.get("SATQUERY_ROUTER_MODEL"):
            explicit_env = os.environ.get("SATQUERY_ROUTER_MODEL")
        elif role == "lightweight" and os.environ.get("SATQUERY_LIGHT_MODEL"):
            explicit_env = os.environ.get("SATQUERY_LIGHT_MODEL")

        running = running_models if running_models is not None else cls.probe_running_models()
        installed = installed_models if installed_models is not None else cls.probe_installed_models()

        if not installed and not running:
            fallback_label = explicit_env if (explicit_env and explicit_env != "auto") else "local-llm"
            return fallback_label, False

        # If user explicitly specified a model name, prioritize it
        if explicit_env and explicit_env != "auto":
            for m in (running + installed):
                if m == explicit_env or m.startswith(explicit_env.split(":")[0]):
                    return m, True
            return explicit_env, True

        # Prioritize whichever model the developer already has running in memory
        if running:
            return running[0], True

        # If only 1 model is installed, use it for all roles
        if len(installed) == 1:
            return installed[0], True

        # If multiple models are installed, allocate appropriately if sizes differ
        if role == "planner":
            for m in installed:
                if any(tag in m.lower() for tag in ["9b", "8b", "7b", "14b", "large"]):
                    return m, True
            return installed[0], True
        elif role in ("fast_router", "lightweight"):
            for m in installed:
                if any(tag in m.lower() for tag in ["0.5b", "1b", "1.5b", "2b", "3b", "4b", "mini", "small"]):
                    return m, True
            return installed[-1], True

        return installed[0], True

    @classmethod
    def get_all_specs(cls) -> Dict[str, ModelSpec]:
        """Returns the full registry status with availability indicators."""
        cls._refresh_cache()
        installed = cls._cached_installed
        running = cls._cached_running
        specs = {}
        for role, defn in cls.MODEL_DEFINITIONS.items():
            active_tag, available = cls.resolve_model_for_role(role, running_models=running, installed_models=installed)
            specs[role] = ModelSpec(
                role=role,
                default_model=defn["default_model"],
                description=defn["description"],
                context_window=defn["context_window"],
                temperature=defn["temperature"],
                active_model=active_tag,
                is_available=available
            )
        return specs

    @classmethod
    def get_active_model(cls) -> Optional[ModelSpec]:
        """Returns the primary active planner model spec."""
        specs = cls.get_all_specs()
        for role in ["planner", "fast_router", "lightweight"]:
            s = specs.get(role)
            if s and s.is_available:
                return s
        return specs.get("planner")

    @classmethod
    def get_status_summary(cls) -> Dict[str, Any]:
        """Holistic summary of local LLM infrastructure for /api/v1/llm-status."""
        cls._refresh_cache()
        online = cls._cached_online
        running = cls._cached_running
        installed = cls._cached_installed
        specs = cls.get_all_specs()

        return {
            "ollama_connected": online,
            "ollama_host": cls.get_ollama_host(),
            "running_models": running,
            "installed_models": installed,
            "model_count": len(installed),
            "cloud_llm": False,  # Strict air-gapped requirement
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

local_registry = LocalModelRegistry
