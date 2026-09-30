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
