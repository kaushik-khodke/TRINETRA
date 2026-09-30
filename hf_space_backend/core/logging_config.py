"""
TRINETRA — Structured JSON Logging & Observability
SIH 2026 • Problem Statement 26167 • Indian Space Research Organisation (ISRO)

Emits machine-parsable JSON logs with request_id, module, timestamp, and performance metrics.
"""

import json
import logging
import datetime
from typing import Optional, Dict, Any


class JSONLogFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "request_id") and record.request_id:
            log_payload["request_id"] = record.request_id

        if hasattr(record, "duration_ms") and record.duration_ms is not None:
            log_payload["duration_ms"] = round(float(record.duration_ms), 2)

        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_payload.update(record.extra_data)

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload)


def setup_structured_logging(level: int = logging.INFO) -> logging.Logger:
    """Configures root TRINETRA structured logger."""
    logger = logging.getLogger("trinetra")
    logger.setLevel(level)

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONLogFormatter())
        logger.addHandler(handler)

    return logger


logger = setup_structured_logging()
