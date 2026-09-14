"""
SatQuery AI — Langfuse Observability & Telemetry Service
Instruments multi-step agent reasoning, specialist tools, and local LLM generations
following Langfuse best practices:
- Descriptive, stable trace & observation names (action-oriented, low cardinality)
- Specific observation types ('agent' for specialists, 'tool' for operations, 'generation' for LLMs)
- Token usage tracking (input_tokens, output_tokens, total_tokens)
- Local model metadata (model tag, latency, role)
- ContextVar-based trace context propagation
- Sensitive filesystem path sanitization (zero PII / path leakage)
- Zero-crash offline fallback when Langfuse server is offline
- Explicit client.flush() on completion
"""

import os
import re
import time
import uuid
import socket
import logging
from urllib.parse import urlparse
from typing import Optional, Dict, Any, List, Union
from contextlib import contextmanager
from contextvars import ContextVar

logger = logging.getLogger("SatQuery.Observability")

# Ensure environment variables are loaded from backend/.env
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_env_path):
    try:
        with open(_env_path, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    _k = _k.strip()
                    _v = _v.strip().strip('"').strip("'")
                    os.environ[_k] = _v
    except Exception:
        pass

try:
    from langfuse import Langfuse
    HAS_LANGFUSE = True
    try:
        from langfuse.model import ModelUsage
    except Exception:
        ModelUsage = None
except ImportError:
    HAS_LANGFUSE = False
    ModelUsage = None

# Thread-safe and async-safe context propagation
_current_trace_context: ContextVar[Optional["AgentTraceContext"]] = ContextVar("satquery_trace_ctx", default=None)


def sanitize_payload(obj: Any) -> Any:
    """
    Sanitizes data payloads for trace telemetry:
    - Replaces local absolute Windows/POSIX filesystem paths with basenames
    - Masks potential secrets, keys, and tokens
    """
    if isinstance(obj, str):
        # Mask local Windows / Linux filesystem paths to basename
        if ("\\" in obj or "/" in obj) and len(obj) > 3:
            # Check if it looks like a filepath (has extension or drive letter)
            if re.search(r"^[a-zA-Z]:[\\/]", obj) or obj.startswith("/") or re.search(r"\.(tif|tiff|png|jpg|jpeg|json|html|csv|txt)$", obj, re.IGNORECASE):
                return os.path.basename(obj.replace("\\", "/"))
        return obj
    elif isinstance(obj, list):
        return [sanitize_payload(item) for item in obj]
    elif isinstance(obj, dict):
        sanitized = {}
        for k, v in obj.items():
            # Mask secret keys if any
            if any(s in k.lower() for s in ["key", "secret", "token", "password"]):
                sanitized[k] = "[MASKED]"
            else:
                sanitized[k] = sanitize_payload(v)
        return sanitized
    return obj


class SafeSpan:
    """
    Safe wrapper around Langfuse span/observation that never fails if telemetry is offline.
    Supports nesting child tools, subagents, and generations.
    """
    def __init__(self, raw_span: Any = None, client: Any = None):
        self.raw_span = raw_span
        self.client = client

    def update(self, output: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None):
        if self.raw_span:
            try:
                self.raw_span.update(
                    output=sanitize_payload(output) if output is not None else None,
                    metadata=sanitize_payload(metadata) if metadata is not None else None
                )
            except Exception:
                pass

    def end(self, **kwargs):
        if self.raw_span:
            try:
                if "output" in kwargs and kwargs["output"] is not None:
                    kwargs["output"] = sanitize_payload(kwargs["output"])
                if "metadata" in kwargs and kwargs["metadata"] is not None:
                    kwargs["metadata"] = sanitize_payload(kwargs["metadata"])
                self.raw_span.end(**kwargs)
            except Exception:
                pass

    @contextmanager
    def tool(self, name: str, input_data: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None):
        """Creates a child tool observation nested inside this observation."""
        child_span = None
        t0 = time.time()
        if self.raw_span:
            try:
                tool_meta = {"observation_type": "tool", "type": "tool", **(metadata or {})}
                child_span = self.raw_span.span(
                    name=name,
                    input=sanitize_payload(input_data),
                    metadata=sanitize_payload(tool_meta)
                )
            except Exception:
                child_span = None

        safe = SafeSpan(child_span, client=self.client)
        try:
            yield safe
        except Exception as exc:
            safe.end(output={"error": str(exc)}, level="ERROR", status_message=str(exc))
            raise
        else:
            duration_ms = (time.time() - t0) * 1000.0
            safe.end(metadata={"duration_ms": round(duration_ms, 2)})

    def record_generation(
        self,
        name: str,
        model: str,
        prompt: str,
        completion: str,
        latency_ms: float,
        usage: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Records an LLM generation nested under this observation."""
        if self.raw_span:
            try:
                gen_usage = None
                if usage and isinstance(usage, dict):
                    if ModelUsage is not None:
                        try:
                            gen_usage = ModelUsage(
                                input=usage.get("input", 0),
                                output=usage.get("output", 0),
                                total=usage.get("total", usage.get("input", 0) + usage.get("output", 0))
                            )
                        except Exception:
                            gen_usage = usage
                    else:
                        gen_usage = usage

                gen_meta = {"latency_ms": latency_ms, **(metadata or {})}
                self.raw_span.generation(
                    name=name,
                    model=model,
                    input=prompt,
                    output=completion,
                    usage=gen_usage,
                    metadata=sanitize_payload(gen_meta)
                )
            except Exception as e:
                logger.debug(f"[Observability] SafeSpan generation skipped: {e}")


class AgentTraceContext:
    """
    Wrapper managing hierarchical spans, subagents, and generations inside a single analysis trace.
    Adheres strictly to Langfuse Agent Graph and Observability standards.
    """

    def __init__(self, analysis_id: str, trace_obj: Any, client: Any):
        self.analysis_id = analysis_id
        self.trace_id = f"satquery_analysis_{analysis_id[:8]}"
        self.trace_obj = trace_obj
        self.client = client
        self.active_subagent_span: Optional[SafeSpan] = None

    def update_task(self, task: str):
        """Updates trace name to descriptive action label once planner identifies task."""
        if self.trace_obj:
            try:
                descriptive_name = f"satquery-analysis-{task.replace('_', '-')}"
                self.trace_obj.update(
                    name=descriptive_name,
                    metadata={"classified_task": task}
                )
            except Exception:
                pass

    @contextmanager
    def span(self, name: str, input_data: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for a standard execution span."""
        span_obj = None
        t0 = time.time()
        if self.trace_obj:
            try:
                span_obj = self.trace_obj.span(
                    name=name,
                    input=sanitize_payload(input_data),
                    metadata=sanitize_payload(metadata or {})
                )
            except Exception:
                span_obj = None

        safe = SafeSpan(span_obj, client=self.client)
        try:
            yield safe
        except Exception as exc:
            safe.end(output={"error": str(exc)}, level="ERROR", status_message=str(exc))
            raise
        else:
            duration_ms = (time.time() - t0) * 1000.0
            safe.end(metadata={"duration_ms": round(duration_ms, 2)})

    @contextmanager
    def tool(self, name: str, input_data: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for a tool operation observation."""
        span_obj = None
        t0 = time.time()
        if self.trace_obj:
            try:
                tool_meta = {"observation_type": "tool", "type": "tool", **(metadata or {})}
                span_obj = self.trace_obj.span(
                    name=name,
                    input=sanitize_payload(input_data),
                    metadata=sanitize_payload(tool_meta)
                )
            except Exception:
                span_obj = None

        safe = SafeSpan(span_obj, client=self.client)
        try:
            yield safe
        except Exception as exc:
            safe.end(output={"error": str(exc)}, level="ERROR", status_message=str(exc))
            raise
        else:
            duration_ms = (time.time() - t0) * 1000.0
            safe.end(metadata={"duration_ms": round(duration_ms, 2)})

    @contextmanager
    def agent(self, name: str, input_data: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Context manager for an agent / subagent execution.
        Renders as a dedicated node in the Langfuse Agent Graph.
        """
        span_obj = None
        t0 = time.time()
        if self.trace_obj:
            try:
                agent_meta = {"observation_type": "agent", "type": "agent", **(metadata or {})}
                span_obj = self.trace_obj.span(
                    name=name,
                    input=sanitize_payload(input_data),
                    metadata=sanitize_payload(agent_meta)
                )
            except Exception:
                span_obj = None

        safe = SafeSpan(span_obj, client=self.client)
        prev_subagent = self.active_subagent_span
        self.active_subagent_span = safe
        try:
            yield safe
        except Exception as exc:
            safe.end(output={"error": str(exc)}, level="ERROR", status_message=str(exc))
            raise
        else:
            duration_ms = (time.time() - t0) * 1000.0
            safe.end(metadata={"duration_ms": round(duration_ms, 2)})
        finally:
            self.active_subagent_span = prev_subagent

    def record_generation(
        self,
        name: str,
        model: str,
        prompt: str,
        completion: str,
        latency_ms: float,
        usage: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Records an LLM generation call with token usage, model name, and prompt/response.
        Nests under the active subagent if present, otherwise attaches directly to trace.
        """
        # If active subagent span is open, nest under it
        if self.active_subagent_span and self.active_subagent_span.raw_span:
            self.active_subagent_span.record_generation(
                name=name,
                model=model,
                prompt=prompt,
                completion=completion,
                latency_ms=latency_ms,
                usage=usage,
                metadata=metadata
            )
            return

        if self.trace_obj:
            try:
                gen_usage = None
                if usage and isinstance(usage, dict):
                    if ModelUsage is not None:
                        try:
                            gen_usage = ModelUsage(
                                input=usage.get("input", 0),
                                output=usage.get("output", 0),
                                total=usage.get("total", usage.get("input", 0) + usage.get("output", 0))
                            )
                        except Exception:
                            gen_usage = usage
                    else:
                        gen_usage = usage

                gen_meta = {"latency_ms": latency_ms, **(metadata or {})}
                self.trace_obj.generation(
                    name=name,
                    model=model,
                    input=prompt,
                    output=completion,
                    usage=gen_usage,
                    metadata=sanitize_payload(gen_meta)
                )
            except Exception as e:
                logger.debug(f"[Observability] Trace generation skipped: {e}")

    def record_error(self, error_message: str):
        """Records an error status on the trace."""
        if self.trace_obj:
            try:
                self.trace_obj.update(
                    output={"error": error_message},
                    metadata={"status": "failed", "error": error_message}
                )
            except Exception:
                pass

    def finalize(self, output: Dict[str, Any], status: str = "completed"):
        """Closes the trace with final outputs and flushes telemetry."""
        if self.trace_obj:
            try:
                self.trace_obj.update(
                    output=sanitize_payload(output),
                    metadata={"final_status": status}
                )
                if self.client:
                    self.client.flush()
            except Exception as e:
                logger.debug(f"[Observability] Finalize flush skipped: {e}")


class LangfuseTracer:
    """
    Manages Langfuse trace and span lifecycles with guaranteed safe offline fallback
    and ContextVar-based execution propagation across the agent stack.
    """

    _client = None
    _initialized = False
    _is_connected = False

    @staticmethod
    def _is_server_reachable(url_str: str, timeout_sec: float = 2.0) -> bool:
        """Fast socket probe to verify telemetry endpoint connectivity."""
        try:
            parsed = urlparse(url_str)
            host = parsed.hostname or "localhost"
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout_sec)
            res = sock.connect_ex((host, port))
            sock.close()
            return res == 0
        except Exception:
            return False

    @classmethod
    def get_client(cls) -> Optional[Any]:
        """Lazily initializes and caches the Langfuse client."""
        if cls._initialized:
            return cls._client

        cls._initialized = True
        if not HAS_LANGFUSE:
            logger.warning("[Observability] Langfuse SDK not installed. Tracing running in local-only mode.")
            return None

        # Resolve host URL
        base_url = os.environ.get("LANGFUSE_BASE_URL", "").strip().strip('"').strip("'")
        host_env = os.environ.get("LANGFUSE_HOST", "").strip().strip('"').strip("'")

        # Prefer cloud URL over localhost:3000 if provided
        if "3000" in host_env and "langfuse.com" in base_url:
            host = base_url.rstrip("/")
        else:
            host = (host_env or base_url or "https://us.cloud.langfuse.com").rstrip("/")

        public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "pk-lf-local-satquery").strip('"').strip("'")
        secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "sk-lf-local-satquery").strip('"').strip("'")

        # Only probe socket for local endpoints (avoid false negatives on cloud hosts)
        if "localhost" in host or "127.0.0.1" in host:
            if not cls._is_server_reachable(host, timeout_sec=0.5):
                cls._client = None
                cls._is_connected = False
                print(f"[*] [Observability] Local Langfuse server at {host} not listening. Using resilient local fallback.")
                return None

        try:
            client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host,
                debug=False
            )
            cls._client = client
            cls._is_connected = True
            print(f"[*] [Observability] Langfuse telemetry connected successfully to {host}.")
        except Exception as e:
            print(f"[*] [Observability] Langfuse connection notice: {e}. Operating in resilient local mode.")
            cls._client = None
            cls._is_connected = False

        return cls._client

    @classmethod
    def is_connected(cls) -> bool:
        """Checks whether Langfuse telemetry is currently operational."""
        cls.get_client()
        return cls._is_connected

    @classmethod
    def is_available(cls) -> bool:
        return cls.is_connected()

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Provides status summary for /api/v1/health and observability dashboards."""
        connected = cls.is_connected()
        host = os.environ.get("LANGFUSE_HOST", os.environ.get("LANGFUSE_BASE_URL", "http://localhost:12000"))
        return {
            "connected": connected,
            "host": host,
            "enabled": HAS_LANGFUSE,
            "status_message": "Operational & Monitoring Traces (Langfuse Connected)" if connected else "Offline (Telemetry running locally with safe zero-overhead fallback)"
        }

    @classmethod
    def get_current_context(cls) -> Optional[AgentTraceContext]:
        """Returns the active trace context from the current async/thread execution context."""
        return _current_trace_context.get()

    @classmethod
    def start_trace(
        cls,
        analysis_id: str,
        query: str,
        input_mode: str = "single",
        task: str = "pending",
        session_id: Optional[str] = None,
        user_id: str = "isro-satellite-analyst",
        response_language: str = "en",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentTraceContext:
        """
        Starts a hierarchical trace context for a user analysis request.
        Follows Langfuse best practices:
        - Trace name is descriptive (satquery-satellite-analysis or satquery-analysis-{task})
        - Trace ID retains stable prefix satquery_analysis_{id}
        - Sensitive paths in inputs/metadata are masked
        - Tags include problem statement, mode, task, and language
        """
        client = cls.get_client()
        trace_obj = None

        descriptive_name = f"satquery-analysis-{task.replace('_', '-')}" if task != "pending" else "satquery-satellite-analysis"

        if client:
            try:
                trace_metadata = {
                    "project": "TRINETRA",
                    "problem_statement": "SIH26167",
                    "organization": "ISRO",
                    "input_mode": input_mode,
                    "initial_task": task,
                    "response_language": response_language,
                    **(metadata or {})
                }
                tags = [
                    "satquery-ai",
                    "trinetra",
                    "isro-sih-26167",
                    f"mode:{input_mode}",
                    f"lang:{response_language}"
                ]
                if task and task != "pending":
                    tags.append(f"task:{task}")

                trace_obj = client.trace(
                    id=f"satquery_analysis_{analysis_id[:12]}",
                    name=descriptive_name,
                    session_id=session_id or analysis_id,
                    user_id=user_id,
                    input=sanitize_payload({"query": query, "input_mode": input_mode, "language": response_language}),
                    metadata=sanitize_payload(trace_metadata),
                    tags=tags
                )
            except Exception as e:
                logger.debug(f"[Observability] Failed to create Langfuse trace: {e}")
                trace_obj = None

        return AgentTraceContext(analysis_id=analysis_id, trace_obj=trace_obj, client=client)

    @classmethod
    @contextmanager
    def trace_analysis(
        cls,
        query: str,
        task: str = "pending",
        session_id: Optional[str] = None,
        input_mode: str = "single",
        response_language: str = "en",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for an entire end-to-end analysis request.
        Propagates trace context across threads/coroutines via ContextVar.
        """
        analysis_id = session_id or uuid.uuid4().hex
        ctx = cls.start_trace(
            analysis_id=analysis_id,
            query=query,
            input_mode=input_mode,
            task=task,
            session_id=session_id,
            response_language=response_language,
            metadata=metadata
        )
        token = _current_trace_context.set(ctx)
        try:
            yield ctx
        finally:
            _current_trace_context.reset(token)
            ctx.finalize(output={"status": "completed"})
