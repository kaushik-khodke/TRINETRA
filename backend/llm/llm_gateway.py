"""
TRINETRA / SatQuery AI — Unified Dual LLM Gateway
Supports Option 1 (Cloud LLM API Key: OpenAI, Groq, OpenRouter, Gemini)
with automatic fallback to Option 2 (Local Air-Gapped Ollama: llama3.2).
"""

import os
import time
import json
import urllib.request
import urllib.error
from typing import Optional, Any, Dict, Type, Tuple
from pydantic import BaseModel

from config.settings import settings
from llm.ollama_provider import OllamaProvider
from llm.model_registry import LocalModelRegistry
from llm.schemas import ModelRole


class UnifiedLLMGateway:
    """
    Central gateway arbitrating between Cloud LLM APIs and Local Ollama inference.
    If LLM_API_KEY is supplied, fast cloud inference is prioritized.
    If absent, expired, or unavailable, it transparently falls back to local Ollama.
    """

    @classmethod
    def _normalize_gemini_model(cls, raw_model: Optional[str]) -> str:
        """Normalizes any user-supplied Gemini model string into the official Google API slug."""
        if not raw_model:
            return "gemini-3.5-flash-lite"
        m = raw_model.strip().lower()
        if "3.5" in m and "lite" in m:
            return "gemini-3.5-flash-lite"
        if "3.5" in m:
            return "gemini-3.5-flash"
        if "2.5" in m and "lite" in m:
            return "gemini-2.5-flash-lite"
        if "2.5" in m and "pro" in m:
            return "gemini-2.5-pro"
        if "2.5" in m:
            return "gemini-2.5-flash"
        if "1.5" in m and "pro" in m:
            return "gemini-1.5-pro"
        if "1.5" in m:
            return "gemini-1.5-flash"
        return m.replace(" ", "-")

    @classmethod
    def resolve_cloud_config(cls) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Resolves (api_key, base_url, model) from settings and environment.
        Supports OpenAI, Groq, OpenRouter, Gemini (including AQ. and AIza keys),
        and generic OpenAI-compatible APIs.
        """
        api_key = (
            settings.llm_api_key
            or os.getenv("LLM_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("GROQ_API_KEY")
            or os.getenv("GEMINI_API_KEY")
        )
        if not api_key or not api_key.strip():
            return None, None, None

        api_key = api_key.strip()
        provider = (settings.llm_provider or os.getenv("LLM_PROVIDER", "auto")).lower()
        custom_base = settings.llm_base_url or os.getenv("LLM_BASE_URL")
        model = settings.llm_model or os.getenv("LLM_MODEL")

        if custom_base:
            base_url = custom_base.rstrip("/")
            if "generativelanguage.googleapis.com" in base_url or (model and "gemini" in model.lower()):
                model = cls._normalize_gemini_model(model or "gemini-3.5-flash-lite")
            else:
                model = model or "gpt-4o-mini"
            return api_key, base_url, model

        # Auto-detect provider based on key prefix, model name, or provider setting
        if provider == "groq" or api_key.startswith("gsk_"):
            base_url = "https://api.groq.com/openai/v1"
            model = model or "llama-3.3-70b-versatile"
        elif provider == "openrouter" or api_key.startswith("sk-or-"):
            base_url = "https://openrouter.ai/api/v1"
            model = model or "openai/gpt-4o-mini"
        elif (
            provider in ("gemini", "google")
            or api_key.startswith("AIza")
            or api_key.startswith("AQ.")
            or (model and "gemini" in model.lower())
        ):
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
            model = cls._normalize_gemini_model(model or "gemini-3.5-flash-lite")
        else:
            # Default to standard OpenAI endpoint
            base_url = "https://api.openai.com/v1"
            model = model or "gpt-4o-mini"

        return api_key, base_url, model

    @classmethod
    def generate_structured(
        cls,
        prompt: str,
        schema: Type[BaseModel],
        role: ModelRole = "planner",
        system_prompt: Optional[str] = None,
        timeout: Optional[float] = None,
        temperature: float = 0.0,
    ) -> Optional[BaseModel]:
        """
        Generates structured Pydantic schema instance using Cloud API if key is present,
        otherwise falls back to Local Ollama.
        """
        api_key, base_url, model = cls.resolve_cloud_config()
        t0 = time.time()
        req_timeout = timeout or settings.llm_timeout

        # ---------------------------------------------------------------------
        # OPTION 1: Cloud LLM API (if API key is present)
        # ---------------------------------------------------------------------
        if api_key and base_url and model:
            try:
                result = cls._call_cloud_openai_compatible(
                    api_key=api_key,
                    base_url=base_url,
                    model=model,
                    prompt=prompt,
                    schema=schema,
                    system_prompt=system_prompt,
                    timeout=req_timeout,
                    temperature=temperature,
                )
                if result:
                    latency = round((time.time() - t0) * 1000.0, 2)
                    print(f"[UnifiedLLMGateway] Cloud LLM ({model}) executed structured generation in {latency}ms.")
                    return result
                print(f"[UnifiedLLMGateway] Cloud LLM returned empty result. Falling back to local Ollama...")
            except urllib.error.HTTPError as http_err:
                err_detail = ""
                try:
                    err_detail = http_err.read().decode("utf-8", errors="ignore")
                except Exception:
                    pass
                print(f"[UnifiedLLMGateway] Cloud LLM HTTP {http_err.code} Error ({err_detail}). Falling back to local Ollama...")
            except Exception as cloud_err:
                print(f"[UnifiedLLMGateway] Cloud LLM request failed ({cloud_err}). Falling back to local Ollama...")

        # ---------------------------------------------------------------------
        # OPTION 2: Local Ollama Fallback
        # ---------------------------------------------------------------------
        return OllamaProvider.generate_structured_native(
            prompt=prompt,
            schema=schema,
            role=role,
            system_prompt=system_prompt,
            timeout=req_timeout,
            temperature=temperature,
        )

    @classmethod
    def _call_cloud_openai_compatible(
        cls,
        api_key: str,
        base_url: str,
        model: str,
        prompt: str,
        schema: Type[BaseModel],
        system_prompt: Optional[str],
        timeout: float,
        temperature: float,
    ) -> Optional[BaseModel]:
        """Calls an OpenAI-compatible /chat/completions endpoint with structured JSON output."""
        schema_dict = schema.model_json_schema() if hasattr(schema, "model_json_schema") else schema.schema()
        schema_str = json.dumps(schema_dict, indent=2)

        augmented_system = (
            (system_prompt or "You are TRINETRA's Controlled Geospatial Intelligence Planner.")
            + f"\n\nOUTPUT FORMAT REQUIREMENT:\nYou MUST output strictly valid JSON matching this exact JSON Schema:\n{schema_str}\n"
            + "Return ONLY raw JSON, with no markdown code fences or extraneous text."
        )

        payload: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": augmented_system},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": temperature,
        }

        endpoint = f"{base_url}/chat/completions"
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "Connection": "close",
                "User-Agent": "TRINETRA-ExploreAI/2.2",
            },
        )

        last_err = None
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    choices = data.get("choices", [])
                    if not choices:
                        return None

                    content = choices[0].get("message", {}).get("content", "").strip()
                    if not content:
                        return None

                    # Strip markdown fences if present
                    if content.startswith("```"):
                        content = content.strip("`")
                        if content.startswith("json"):
                            content = content[4:].strip()

                    parsed = json.loads(content)
                    return schema.model_validate(parsed) if hasattr(schema, "model_validate") else schema.parse_obj(parsed)
            except (socket.timeout, TimeoutError, urllib.error.URLError) as e:
                last_err = e
                if attempt == 0:
                    time.sleep(1.0)
                    continue
                raise last_err

    @classmethod
    def get_status_info(cls) -> Dict[str, Any]:
        """Returns status of active LLM runtime (Cloud or Local)."""
        api_key, _, model = cls.resolve_cloud_config()
        if api_key and model:
            return {
                "available": True,
                "mode": "cloud",
                "provider": settings.llm_provider or "cloud",
                "model": model,
                "offline_fallback_active": False,
            }

        ollama_online = LocalModelRegistry.is_ollama_online()
        model_tag, available = LocalModelRegistry.resolve_model_for_role("planner")
        return {
            "available": ollama_online and available,
            "mode": "local",
            "provider": "ollama",
            "model": model_tag,
            "offline_fallback_active": not (ollama_online and available),
        }
