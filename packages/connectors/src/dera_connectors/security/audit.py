"""DERA Connectors — Security Audit Logging & Telemetry.

Captures auditable security events for connector operations, access decisions,
read-only violations, SSRF rejections, and deadline expirations without leaking credentials.
"""

from __future__ import annotations

import datetime
import logging
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from dera_connectors.security.redaction import sanitize_diagnostics

logger = logging.getLogger("dera_connectors.security.audit")

# In-memory circular buffer for security event auditing in test and diagnostic suites
_AUDIT_LOG_BUFFER: list[SecurityAuditEvent] = []
_MAX_AUDIT_BUFFER_SIZE = 500


@dataclass(frozen=True)
class SecurityAuditEvent:
    """Immutable audit record representing a connector security evaluation."""

    workspace_id: str
    engine: str
    operation_id: str
    status: str  # ALLOW, DENY, VIOLATION, TIMEOUT, CANCELLED
    duration_ms: float = 0.0
    user_id: str | None = None
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp_utc: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat()
    )
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert audit event to a sanitized dictionary."""
        data = asdict(self)
        data["details"] = sanitize_diagnostics(self.details)
        return data


def log_security_audit_event(
    workspace_id: str,
    engine: str,
    operation_id: str,
    status: str,
    duration_ms: float = 0.0,
    user_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> SecurityAuditEvent:
    """Record a structured security audit event.

    Parameters
    ----------
    workspace_id : str
        Authenticated tenant workspace.
    engine : str
        Database engine identifier.
    operation_id : str
        Introspection or connection operation identifier.
    status : str
        ALLOW, DENY, VIOLATION, TIMEOUT, CANCELLED.
    duration_ms : float
        Elapsed execution time in milliseconds.
    user_id : str | None
        Optional caller identifier.
    details : dict[str, Any] | None
        Event details (automatically sanitized).

    Returns
    -------
    SecurityAuditEvent
        Created and recorded audit event.
    """
    event = SecurityAuditEvent(
        workspace_id=str(workspace_id),
        engine=str(engine),
        operation_id=str(operation_id),
        status=str(status).upper(),
        duration_ms=float(duration_ms),
        user_id=str(user_id) if user_id else None,
        details=sanitize_diagnostics(details or {}),
    )

    # Append to in-memory buffer
    global _AUDIT_LOG_BUFFER
    _AUDIT_LOG_BUFFER.append(event)
    if len(_AUDIT_LOG_BUFFER) > _MAX_AUDIT_BUFFER_SIZE:
        _AUDIT_LOG_BUFFER = _AUDIT_LOG_BUFFER[-_MAX_AUDIT_BUFFER_SIZE:]

    # Log structured event
    log_level = logging.WARNING if event.status in ("DENY", "VIOLATION") else logging.INFO
    logger.log(
        log_level,
        "SECURITY_AUDIT: [%s] op=%s engine=%s workspace=%s status=%s duration=%.2fms",
        event.event_id,
        event.operation_id,
        event.engine,
        event.workspace_id,
        event.status,
        event.duration_ms,
        extra={"security_event": event.to_dict()},
    )
    return event


def get_recent_audit_events() -> list[SecurityAuditEvent]:
    """Return all recorded in-memory security audit events."""
    return list(_AUDIT_LOG_BUFFER)


def clear_audit_events() -> None:
    """Clear in-memory audit buffer."""
    global _AUDIT_LOG_BUFFER
    _AUDIT_LOG_BUFFER.clear()
