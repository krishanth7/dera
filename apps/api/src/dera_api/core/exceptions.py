"""DERA API — Structured HTTP Exception Handlers.

Maps domain DeraError subclasses to standard JSON HTTP responses.
"""

from typing import Any

from dera_core.exceptions import (
    DeraError,
)


def format_error_response(error: DeraError, status_code: int) -> dict[str, Any]:
    """Format a domain error into standard API error dictionary."""
    return {
        "success": False,
        "status_code": status_code,
        "error": {
            "type": error.__class__.__name__,
            "message": error.message,
            "details": error.details,
        },
    }
