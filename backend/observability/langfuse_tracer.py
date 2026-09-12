import os
import time
import uuid
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

logger = logging.getLogger("SatQuery.Observability")

try:
    from langfuse import Langfuse
    HAS_LANGFUSE = True
except ImportError:
    HAS_LANGFUSE = False

class SafeSpan:
    """Safe wrapper around Langfuse span that never fails if telemetry is offline."""
    def __init__(self, raw_span: Any = None):
        self.raw_span = raw_span

    def update(self, output: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None):
        if self.raw_span:
            try:
                self.raw_span.update(output=output, metadata=metadata)
            except Exception:
                pass

    def end(self, **kwargs):
        if self.raw_span:
            try:
                self.raw_span.end(**kwargs)
            except Exception:
                pass

class LangfuseTracer:
    """Manages Langfuse trace and span lifecycles with guaranteed safe offline fallback."""

    _client = None
    _initialized = False
    _is_connected = False

    @classmethod
    def get_client(cls) -> Optional[Any]:
        """Lazily initializes and caches the Langfuse client."""
        if cls._initialized:
            return cls._client

        cls._initialized = True
        if not HAS_LANGFUSE:
            logger.warning("[Observability] Langfuse SDK not installed. Tracing running in local-only mode.")
            return None

        host = os.environ.get("LANGFUSE_HOST", "http://localhost:12000").rstrip("/")
        public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "pk-lf-local-satquery")
        secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "sk-lf-local-satquery")

        try:
            client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host,
                debug=False
            )
            # Lightweight health ping
            client.auth_check()
            cls._client = client
            cls._is_connected = True
            logger.info(f"[Observability] Langfuse telemetry connected successfully to {host}.")
        except Exception as e:
            logger.warning(f"[Observability] Langfuse server at {host} unreachable ({e}). Continuing with zero-impact fallback.")
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
        """Provides status summary for /api/v1/health."""
        connected = cls.is_connected()
        host = os.environ.get("LANGFUSE_HOST", "http://localhost:12000")
        return {
            "connected": connected,
            "host": host,
            "enabled": HAS_LANGFUSE,
            "status_message": "Operational & Monitoring Traces" if connected else "Offline (Telemetry running locally without cloud dependency)"
        }

    @classmethod
    def start_trace(
        cls,
        analysis_id: str,
        query: str,
        input_mode: str = "single",
        task: str = "pending",
        metadata: Optional[Dict[str, Any]] = None
    ) -> "AgentTraceContext":
        """Starts a hierarchical trace context for a user analysis request."""
        client = cls.get_client()
        trace_obj = None

        if client:
            try:
                trace_metadata = {
                    "project": "TRINETRA",
                    "problem_statement": "SIH26167",
                    "organization": "ISRO",
                    "input_mode": input_mode,
                    "task": task,
                    **(metadata or {})
                }
                trace_obj = client.trace(
                    id=f"satquery_analysis_{analysis_id[:12]}",
                    name=f"satquery_analysis_{analysis_id[:8]}",
                    input={"query": query, "mode": input_mode},
                    metadata=trace_metadata,
                    tags=["satquery-ai", "local-agent", input_mode, task]
                )
            except Exception as e:
                logger.warning(f"[Observability] Failed to create Langfuse trace: {e}")
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
        metadata: Optional[Dict[str, Any]] = None
    ):
        analysis_id = session_id or uuid.uuid4().hex
        ctx = cls.start_trace(
            analysis_id=analysis_id,
            query=query,
            input_mode=input_mode,
            task=task,
            metadata=metadata
        )
        try:
            yield ctx
        finally:
            ctx.finalize(output={"status": "completed"})

class AgentTraceContext:
    """Wrapper managing spans and generations inside a single analysis trace."""

    def __init__(self, analysis_id: str, trace_obj: Any, client: Any):
        self.analysis_id = analysis_id
        self.trace_id = f"satquery_analysis_{analysis_id[:8]}"
        self.trace_obj = trace_obj
        self.client = client
        self.spans: Dict[str, Any] = {}

    @contextmanager
    def span(self, name: str, input_data: Optional[Any] = None, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for an execution span returning a SafeSpan."""
        span_obj = None
        t0 = time.time()

        if self.trace_obj:
            try:
                span_obj = self.trace_obj.span(
                    name=name,
                    input=input_data,
                    metadata=metadata or {}
                )
            except Exception:
                span_obj = None

        safe = SafeSpan(span_obj)
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
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Records an LLM generation call."""
        if self.trace_obj:
            try:
                self.trace_obj.generation(
                    name=name,
                    model=model,
                    input=prompt,
                    output=completion,
                    metadata={"latency_ms": latency_ms, **(metadata or {})}
                )
            except Exception as e:
                logger.warning(f"[Observability] Failed to record generation: {e}")

    def record_error(self, error_message: str):
        """Records an error status on the trace."""
        if self.trace_obj:
            try:
                self.trace_obj.update(output={"error": error_message}, metadata={"status": "failed"})
            except Exception:
                pass

    def finalize(self, output: Dict[str, Any], status: str = "completed"):
        """Closes the trace with final outputs."""
        if self.trace_obj:
            try:
                self.trace_obj.update(
                    output=output,
                    metadata={"final_status": status}
                )
                if self.client:
                    self.client.flush()
            except Exception as e:
                logger.warning(f"[Observability] Failed to finalize Langfuse trace: {e}")

