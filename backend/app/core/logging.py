from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

# Context variables for request-scoped data
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
report_id_ctx: ContextVar[str | None] = ContextVar("report_id", default=None)
job_id_ctx: ContextVar[str | None] = ContextVar("job_id", default=None)


class StructuredJsonFormatter(logging.Formatter):
    """JSON formatter that never logs raw media, tokens, or PII."""

    SENSITIVE_KEYS = {
        "password", "token", "api_key", "secret", "authorization",
        "model_api_key", "aws_secret_key", "private_key", "credential",
    }

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add context variables
        rid = request_id_ctx.get()
        if rid:
            log_data["request_id"] = rid
        rpid = report_id_ctx.get()
        if rpid:
            log_data["report_id"] = rpid
        jid = job_id_ctx.get()
        if jid:
            log_data["job_id"] = jid

        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "taskName",
                "message",
            }:
                if key.lower() in self.SENSITIVE_KEYS:
                    log_data[key] = "[REDACTED]"
                else:
                    log_data[key] = value

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str)


def setup_logging(level: str = "INFO") -> None:
    """Configure structured JSON logging for the application."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]

    # Reduce noise from libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def set_request_id(rid: str) -> None:
    request_id_ctx.set(rid)


def set_report_id(rpid: str) -> None:
    report_id_ctx.set(rpid)


def set_job_id(jid: str) -> None:
    job_id_ctx.set(jid)
