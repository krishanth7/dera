"""DERA Connectors — Unified Security, Isolation & Safety Subsystem.

Provides comprehensive read-only enforcement, SSRF defense, filesystem containment,
workspace isolation, centralized timeouts, cancellation tokens, resource bounds,
credential redaction, and security audit logging.
"""

from __future__ import annotations

from dera_connectors.security.audit import (
    SecurityAuditEvent,
    clear_audit_events,
    get_recent_audit_events,
    log_security_audit_event,
)
from dera_connectors.security.authorization import (
    AuthorizationEnforcementPipeline,
    validate_workspace_authorization,
)
from dera_connectors.security.cancellation import (
    EnhancedCancellationToken,
)
from dera_connectors.security.credentials import (
    DatabaseCredentials,
    SecureCredentialResolver,
)
from dera_connectors.security.destinations import (
    resolve_and_validate_destination,
    validate_network_target,
    verify_destination_pinning,
)
from dera_connectors.security.errors import (
    CancellationRequestedViolationError,
    ConnectorSecurityError,
    CredentialExposureError,
    DNSRebindingViolationError,
    FilesystemIsolationViolationError,
    ReadOnlySecurityViolationError,
    ResourceLimitExceededViolationError,
    SSRFSecurityViolationError,
    TenantIsolationViolationError,
    TimeoutExceededViolationError,
    UnauthorizedQueryError,
)
from dera_connectors.security.isolation import (
    build_sqlite_readonly_uri,
    validate_filesystem_target,
)
from dera_connectors.security.policy import (
    ConnectorSecurityPolicy,
)
from dera_connectors.security.query_policy import (
    GLOBAL_QUERY_REGISTRY,
    ApprovedMetadataQueryRegistry,
    QuerySpecification,
)
from dera_connectors.security.readonly import (
    assert_read_only_transaction,
    strip_sql_comments_and_literals,
    validate_read_only_sql,
)
from dera_connectors.security.redaction import (
    mask_sensitive_strings,
    redact_credentials,
    safe_log_record,
    sanitize_diagnostics,
)
from dera_connectors.security.resource_limits import (
    ConnectorResourceLimits,
)
from dera_connectors.security.timeouts import (
    DeadlineTracker,
    TimeoutBudget,
)

__all__ = [
    # Errors
    "ConnectorSecurityError",
    "ReadOnlySecurityViolationError",
    "SSRFSecurityViolationError",
    "DNSRebindingViolationError",
    "FilesystemIsolationViolationError",
    "TenantIsolationViolationError",
    "TimeoutExceededViolationError",
    "CancellationRequestedViolationError",
    "ResourceLimitExceededViolationError",
    "UnauthorizedQueryError",
    "CredentialExposureError",
    # Redaction
    "mask_sensitive_strings",
    "sanitize_diagnostics",
    "redact_credentials",
    "safe_log_record",
    # Read-Only
    "validate_read_only_sql",
    "strip_sql_comments_and_literals",
    "assert_read_only_transaction",
    # Query Policy
    "QuerySpecification",
    "ApprovedMetadataQueryRegistry",
    "GLOBAL_QUERY_REGISTRY",
    # Destinations & SSRF
    "validate_network_target",
    "resolve_and_validate_destination",
    "verify_destination_pinning",
    # Credentials
    "DatabaseCredentials",
    "SecureCredentialResolver",
    # Authorization & Multi-Tenancy
    "validate_workspace_authorization",
    "AuthorizationEnforcementPipeline",
    # Timeouts & Deadlines
    "TimeoutBudget",
    "DeadlineTracker",
    # Cancellation
    "EnhancedCancellationToken",
    # Resource Limits
    "ConnectorResourceLimits",
    # Filesystem & SQLite Isolation
    "validate_filesystem_target",
    "build_sqlite_readonly_uri",
    # Audit Logging
    "SecurityAuditEvent",
    "log_security_audit_event",
    "get_recent_audit_events",
    "clear_audit_events",
    # Unified Policy
    "ConnectorSecurityPolicy",
]
