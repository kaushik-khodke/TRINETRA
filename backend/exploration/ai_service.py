"""
TRINETRA / Shanetra Geospatial Exploration Engine
AI Exploration Service & Multi-Stage Orchestrator
Phase 3: Natural-Language Earth Exploration + Controlled AI Map Commands
Coordinates Fast-Path deterministic parser, local intent classification, structured planning,
multi-tier policy validation, and sequential command execution.
"""

import time
import uuid
import socket
from typing import Any, Dict, List, Optional
from exploration.ai_schemas import (
    ExploreAIQueryRequest,
    ExploreAIQueryResponse,
    ExploreAIStatusResponse,
    ExploreCommandPlan,
    ExploreIntent,
    ExploreIntentType,
    CommandExecutionItem,
    CommandExecutionStatus,
    ExploreStatePatch,
    EXPLORE_QUERY_EMPTY,
    EXPLORE_QUERY_TOO_LONG,
    EXPLORE_INTENT_UNKNOWN,
    EXPLORE_LLM_TIMEOUT,
    EXPLORE_LLM_INVALID_OUTPUT,
    EXPLORE_COMMAND_REJECTED,
)
from exploration.fallback_parser import FallbackParser
from exploration.command_validator import CommandValidator
from exploration.command_executor import CommandExecutor
from exploration.command_normalizer import CommandNormalizer
from exploration.prompts import (
    INTENT_CLASSIFIER_SYSTEM_PROMPT,
    COMMAND_PLANNER_SYSTEM_PROMPT,
    build_intent_prompt,
    build_planner_prompt,
)
from exploration.service import explore_service
from llm.model_registry import LocalModelRegistry
from llm.ollama_provider import OllamaProvider


class ExploreAIService:
    """End-to-end coordinator for Shanetra's natural language command pipeline."""

    def __init__(self):
        pass

    def get_status(self) -> ExploreAIStatusResponse:
        """Returns the operational status of local LLMs and structured generation capability."""
        online = LocalModelRegistry.is_ollama_online()
        router_tag, router_avail = LocalModelRegistry.resolve_model_for_role("fast_router")
        planner_tag, planner_avail = LocalModelRegistry.resolve_model_for_role("planner")

        is_available = online and (router_avail or planner_avail)

        return ExploreAIStatusResponse(
            available=is_available,
            model=planner_tag,
            router_model=router_tag,
            planner_model=planner_tag,
            structured_output=True,
            offline_fallback_active=not is_available,
        )

    def process_query(self, request: ExploreAIQueryRequest) -> ExploreAIQueryResponse:
        """
        Processes a natural-language exploration query through the guarded AI gateway.
        Guarantees response within strict timeouts and deterministic fallbacks.
        """
        t0 = time.time()
        req_id = f"exp_{uuid.uuid4().hex[:8]}"

        # 1. Input Sanitization & Guardrails
        raw_query = request.query.strip() if request.query else ""
        if not raw_query:
            return self._build_error_response(
                req_id=req_id,
                error_code=EXPLORE_QUERY_EMPTY,
                summary="Query cannot be empty. Try asking 'Go to Nagpur' or 'Show Sentinel-2'.",
                t0=t0,
            )

        if len(raw_query) > 500:
            return self._build_error_response(
                req_id=req_id,
                error_code=EXPLORE_QUERY_TOO_LONG,
                summary="Query exceeds maximum allowed length of 500 characters.",
                t0=t0,
            )

        active_layer_ids = list(request.active_layer_ids or [])
        current_camera = request.view_state.model_dump() if request.view_state else None

        # 2. FAST PATH: Deterministic Fallback Parser (< 1ms execution, 0 LLM calls)
        fallback_plan = FallbackParser.parse(raw_query)
        if fallback_plan:
            valid, err_code, err_msg = CommandValidator.validate_plan(fallback_plan, active_layer_ids)
            if valid:
                status, items, patch, exec_err = CommandExecutor.execute_plan(
                    plan=fallback_plan,
                    current_active_layers=active_layer_ids,
                    current_camera=current_camera,
                )
                summary = CommandExecutor.generate_user_summary(items)
                latency = (time.time() - t0) * 1000.0
                return ExploreAIQueryResponse(
                    request_id=req_id,
                    status=status,
                    summary=summary,
                    intent=fallback_plan.intent,
                    fast_path=True,
                    commands=items,
                    state_patch=patch,
                    error_code=exec_err,
                    latency_ms=round(latency, 2),
                )

        # 3. AI PATH: Verify local Ollama availability
        if not LocalModelRegistry.is_ollama_online():
            return ExploreAIQueryResponse(
                request_id=req_id,
                status="rejected",
                summary="Local Ollama service is offline. Basic commands ('reset', 'zoom in', 'show boundaries') remain active via deterministic fallback.",
                intent="unsupported",
                fast_path=False,
                commands=[],
                state_patch=ExploreStatePatch(visible_layer_ids=active_layer_ids),
                error_code="EXPLORE_PROVIDER_UNAVAILABLE",
                latency_ms=round((time.time() - t0) * 1000.0, 2),
            )

        # 4. Stage A: Fast Intent Classification (role: fast_router)
        intent_prompt = build_intent_prompt(raw_query, current_camera)
        try:
            intent_obj: Optional[ExploreIntent] = OllamaProvider.generate_structured_native(
                prompt=intent_prompt,
                schema=ExploreIntent,
                role="fast_router",
                system_prompt=INTENT_CLASSIFIER_SYSTEM_PROMPT,
                timeout=12.0,
                temperature=0.0,
            )
        except (socket.timeout, TimeoutError):
            return self._build_error_response(
                req_id=req_id,
                error_code=EXPLORE_LLM_TIMEOUT,
                summary="Intent classification timed out.",
                t0=t0,
            )
        except Exception:
            intent_obj = None

        if not intent_obj:
            return self._build_error_response(
                req_id=req_id,
                error_code=EXPLORE_LLM_INVALID_OUTPUT,
                summary="Failed to classify exploration intent. Please rephrase or use simple controls.",
                t0=t0,
            )

        # 5. Guardrail: Defer deep scientific analysis requests (VQA, change detection, NDVI, flooding)
        if intent_obj.intent == ExploreIntentType.UNSUPPORTED:
            reason = intent_obj.unsupported_reason or (
                "This request requires TRINETRA's deep Earth-observation analytical models (VQA, change detection, or NDVI), "
                "which will be enabled in subsequent workstation phases."
            )
            return ExploreAIQueryResponse(
                request_id=req_id,
                status="rejected",
                summary=reason,
                intent="unsupported",
                fast_path=False,
                commands=[],
                state_patch=ExploreStatePatch(visible_layer_ids=active_layer_ids),
                error_code=None,
                latency_ms=round((time.time() - t0) * 1000.0, 2),
            )

        # 6. Stage B: Structured Command Planning (role: planner)
        available_layers = [
            {"id": l.id, "name": l.name}
            for l in explore_service.list_layers()
            if l.ai_controllable and l.enabled
        ]
        planner_prompt = build_planner_prompt(
            query=raw_query,
            intent=intent_obj,
            available_layers=available_layers,
            active_layers=active_layer_ids,
            current_view=current_camera,
        )

        try:
            plan: Optional[ExploreCommandPlan] = OllamaProvider.generate_structured_native(
                prompt=planner_prompt,
                schema=ExploreCommandPlan,
                role="planner",
                system_prompt=COMMAND_PLANNER_SYSTEM_PROMPT,
                timeout=25.0,
                temperature=0.0,
            )
        except (socket.timeout, TimeoutError):
            return self._build_error_response(
                req_id=req_id,
                error_code=EXPLORE_LLM_TIMEOUT,
                summary="Command planning timed out.",
                t0=t0,
            )
        except Exception:
            plan = None

        if not plan:
            return self._build_error_response(
                req_id=req_id,
                error_code=EXPLORE_LLM_INVALID_OUTPUT,
                summary="Command planner could not produce a valid map action plan.",
                t0=t0,
            )

        # Deduplicate commands if normalizer finds repeats
        plan.commands = CommandNormalizer.deduplicate_commands(plan.commands)

        # 7. Command Validation Pipeline
        valid, val_err_code, val_err_msg = CommandValidator.validate_plan(plan, active_layer_ids)
        if not valid:
            return ExploreAIQueryResponse(
                request_id=req_id,
                status="rejected",
                summary=f"Command validation rejected: {val_err_msg}",
                intent=intent_obj.intent.value,
                fast_path=False,
                commands=[
                    CommandExecutionItem(
                        command_id="cmd_000",
                        type="PLAN",
                        status=CommandExecutionStatus.REJECTED,
                        message=val_err_msg or "Plan failed validation checks.",
                    )
                ],
                state_patch=ExploreStatePatch(visible_layer_ids=active_layer_ids),
                error_code=val_err_code or EXPLORE_COMMAND_REJECTED,
                latency_ms=round((time.time() - t0) * 1000.0, 2),
            )

        # 8. Execution Phase
        exec_status, exec_items, patch, exec_err = CommandExecutor.execute_plan(
            plan=plan,
            current_active_layers=active_layer_ids,
            current_camera=current_camera,
        )

        # 9. Deterministic User Summary
        summary = CommandExecutor.generate_user_summary(exec_items)
        latency = (time.time() - t0) * 1000.0

        return ExploreAIQueryResponse(
            request_id=req_id,
            status=exec_status,
            summary=summary,
            intent=intent_obj.intent.value,
            fast_path=False,
            commands=exec_items,
            state_patch=patch,
            error_code=exec_err,
            latency_ms=round(latency, 2),
        )

    def _build_error_response(
        self,
        req_id: str,
        error_code: str,
        summary: str,
        t0: float,
    ) -> ExploreAIQueryResponse:
        return ExploreAIQueryResponse(
            request_id=req_id,
            status="error",
            summary=summary,
            intent="unknown",
            fast_path=False,
            commands=[],
            state_patch=ExploreStatePatch(),
            error_code=error_code,
            latency_ms=round((time.time() - t0) * 1000.0, 2),
        )


# Singleton service export
explore_ai_service = ExploreAIService()
