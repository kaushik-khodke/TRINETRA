"""
TRINETRA — API Reliability, Request ID & RFC 7807 Middleware
SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)

Production hardening middleware:
1. Injects and tracks X-Request-ID across the entire request/response lifecycle
2. Enforces configurable asynchronous timeouts with clean cancellation
3. Formats all exceptions as RFC 7807 Problem Details JSON payloads
"""

import time
import uuid
import asyncio
import datetime
import collections
import threading
from typing import Optional, Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from core.logging_config import logger
from core.exceptions import TRINETRABaseException, SecurityViolationError


def format_rfc7807_error(
    status_code: int,
    title: str,
    detail: str,
    request_id: Optional[str] = None,
    error_code: Optional[str] = None,
    remediation: Optional[str] = None,
    instance: Optional[str] = None
) -> JSONResponse:
    """Constructs a compliant RFC 7807 Problem Details JSON response."""
    payload = {
        "type": f"https://trinetra.isro.gov.in/errors/{error_code or 'ERR_HTTP_ERROR'}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": instance or "/",
        "request_id": request_id or str(uuid.uuid4()),
        "error_code": error_code or "ERR_HTTP_ERROR",
        "remediation": remediation or "Inspect request headers and parameters.",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    headers = {"Content-Type": "application/problem+json"}
    if request_id:
        headers["X-Request-ID"] = request_id
    return JSONResponse(status_code=status_code, content=payload, headers=headers)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assigns or propagates X-Request-ID and logs request latency."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract or generate request ID
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = req_id

        t0 = time.time()
        try:
            response = await call_next(request)
            duration_ms = (time.time() - t0) * 1000.0
            response.headers["X-Request-ID"] = req_id

            logger.info(
                f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)",
                extra={"request_id": req_id, "duration_ms": duration_ms}
            )
            return response
        except Exception as exc:
            duration_ms = (time.time() - t0) * 1000.0
            logger.error(
                f"{request.method} {request.url.path} FAILED: {exc}",
                exc_info=True,
                extra={"request_id": req_id, "duration_ms": duration_ms}
            )
            raise


class TimeoutMiddleware(BaseHTTPMiddleware):
    """Enforces execution timeouts on long-running analysis endpoints."""

    def __init__(self, app, timeout_seconds: float = 60.0):
        super().__init__(app)
        self.timeout_seconds = timeout_seconds

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        try:
            return await asyncio.wait_for(call_next(request), timeout=self.timeout_seconds)
        except asyncio.TimeoutError:
            logger.warning(
                f"Request {request.url.path} timed out after {self.timeout_seconds}s",
                extra={"request_id": req_id}
            )
            return format_rfc7807_error(
                status_code=504,
                title="Gateway Timeout",
                detail=f"Execution exceeded maximum allowed timeout of {self.timeout_seconds} seconds.",
                request_id=req_id,
                error_code="ERR_EXECUTION_TIMEOUT",
                remediation="Reduce raster dimensions or run on GPU accelerated device.",
                instance=request.url.path
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    In-memory sliding-window rate limiter.
    Protects against DoS, brute-force scraping, and model execution flooding.
    Respects X-Forwarded-For (from Vercel / Cloudflare edge proxy) and request.client.host.
    """
    def __init__(
        self,
        app,
        global_rate_limit: int = 60,
        heavy_rate_limit: int = 10,
        window_seconds: int = 60
    ):
        super().__init__(app)
        self.global_rate_limit = global_rate_limit
        self.heavy_rate_limit = heavy_rate_limit
        self.window_seconds = window_seconds
        self._history = collections.defaultdict(list)
        self._heavy_history = collections.defaultdict(list)
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    def _get_client_ip(self, request: Request) -> str:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            return cf_ip.strip()
        if request.client and request.client.host:
            return request.client.host
        return "127.0.0.1"

    def _is_rate_limited(self, history: list, limit: int, now: float) -> bool:
        cutoff = now - self.window_seconds
        valid = [t for t in history if t > cutoff]
        history.clear()
        history.extend(valid)
        if len(history) >= limit:
            return True
        history.append(now)
        return False

    def _cleanup_old_entries(self, now: float):
        if now - self._last_cleanup > 300:
            cutoff = now - self.window_seconds
            for h in (self._history, self._heavy_history):
                stale_keys = [k for k, v in h.items() if not v or max(v) < cutoff]
                for k in stale_keys:
                    del h[k]
            self._last_cleanup = now

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Health endpoints exempt from strict rate limiting
        if path in ("/healthz", "/readyz", "/api/v1/health"):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        now = time.time()

        with self._lock:
            self._cleanup_old_entries(now)

            # Check global request rate limit
            if self._is_rate_limited(self._history[client_ip], self.global_rate_limit, now):
                req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
                logger.warning(f"Rate limit exceeded (global) for client IP: {client_ip} on {path}")
                return format_rfc7807_error(
                    status_code=429,
                    title="Too Many Requests",
                    detail=f"Rate limit of {self.global_rate_limit} requests per minute exceeded.",
                    request_id=req_id,
                    error_code="ERR_RATE_LIMIT_EXCEEDED",
                    remediation="Slow down requests. Wait 60 seconds before retrying.",
                    instance=path
                )

            # Check heavy inference endpoints limit
            is_heavy = any(path.startswith(p) for p in ("/api/v1/analyze", "/api/v1/inspect-image", "/api/v1/explore/investigations"))
            if is_heavy and self._is_rate_limited(self._heavy_history[client_ip], self.heavy_rate_limit, now):
                req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
                logger.warning(f"Heavy compute rate limit exceeded for client IP: {client_ip} on {path}")
                return format_rfc7807_error(
                    status_code=429,
                    title="Too Many Requests",
                    detail=f"Compute rate limit of {self.heavy_rate_limit} analyses per minute exceeded.",
                    request_id=req_id,
                    error_code="ERR_COMPUTE_RATE_LIMIT_EXCEEDED",
                    remediation="AI reasoning pipeline is busy. Please wait before submitting another satellite analysis.",
                    instance=path
                )

        return await call_next(request)

