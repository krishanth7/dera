"""DERA API — Structured Logging Foundation.

Provides structured console logging with UTC timestamps, request correlation,
and defensive secret redaction filters for containerized execution.
"""

import logging
import re
import sys
from datetime import UTC, datetime

# Patterns to sanitize from log messages
SENSITIVE_PATTERNS = [
    re.compile(
        r"(password|passwd|pwd|secret|token|api_key|apikey|authorization)\s*[:=]\s*['\"]?([^'\"&\s,]+)",
        re.IGNORECASE,
    ),
    re.compile(r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
    re.compile(r"(postgres(?:ql)?://[^:]+:)([^@]+)(@)", re.IGNORECASE),
    re.compile(r"(mysql://[^:]+:)([^@]+)(@)", re.IGNORECASE),
]


class SensitiveDataFilter(logging.Filter):
    """Redacts passwords, tokens, connection secrets, and authorization headers."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.sanitize(record.msg)
        if record.args:
            sanitized_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    sanitized_args.append(self.sanitize(arg))
                else:
                    sanitized_args.append(arg)
            record.args = tuple(sanitized_args)
        return True

    @staticmethod
    def sanitize(text: str) -> str:
        sanitized = text
        for pattern in SENSITIVE_PATTERNS:
            if "postgres" in pattern.pattern or "mysql" in pattern.pattern:
                sanitized = pattern.sub(r"\1***REDACTED***\3", sanitized)
            elif "Bearer" in pattern.pattern:
                sanitized = pattern.sub(r"\1***REDACTED***", sanitized)
            else:
                sanitized = pattern.sub(r"\1=***REDACTED***", sanitized)
        return sanitized


class UtcFormatter(logging.Formatter):
    """Outputs ISO 8601 UTC timestamps with correlation context."""

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        utc_dt = datetime.fromtimestamp(record.created, tz=UTC)
        if datefmt:
            return utc_dt.strftime(datefmt)
        return utc_dt.isoformat()


def configure_logging(log_level: str = "INFO") -> None:
    """Configures application-wide logging with UTC timestamps and secret filters."""
    root_logger = logging.getLogger()
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers if reconfigured
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)

    formatter = UtcFormatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())

    root_logger.addHandler(handler)


def get_logger(name: str = "dera_api") -> logging.Logger:
    """Return a configured logger instance."""
    return logging.getLogger(name)
