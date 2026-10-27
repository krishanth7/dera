"""DERA Connectors — Read-Only Security Policy & Network Boundary Enforcement.

Enforces:
1. Strict read-only query inspection boundaries, rejecting any DDL/DML mutations.
2. Server-Side Request Forgery (SSRF) defenses, blocking cloud metadata endpoints and private networks.
3. Centralized credential sanitization and masking.
"""

import re
from ipaddress import ip_address, ip_network
from typing import Any

# Mutation keywords that violate DERA's deterministic read-only invariant
_MUTATION_KEYWORDS = re.compile(
    r"\b(DROP|TRUNCATE|ALTER|CREATE|INSERT|UPDATE|DELETE|GRANT|REVOKE|REPLACE|EXEC|EXECUTE|VACUUM|REINDEX|LOCK)\b",
    re.IGNORECASE,
)

# Common cloud metadata endpoints and loopback addresses
_BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata.google",
    "169.254.169.254",
    "instance-data",
}

# Standard private and link-local CIDR blocks
_PRIVATE_NETWORKS = [
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
    ip_network("127.0.0.0/8"),
    ip_network("169.254.0.0/16"),  # Link-local / Cloud metadata
    ip_network("::1/128"),  # IPv6 loopback
    ip_network("fc00::/7"),  # IPv6 unique local
    ip_network("fe80::/10"),  # IPv6 link-local
]

# Sensitive regexes for masking connection secrets
_SECRET_URI_REGEX = re.compile(
    r"(://[^:]+:)([^@]+)(@)",
    re.IGNORECASE,
)
_PASSWORD_FIELD_REGEX = re.compile(
    r"(password|secret|token|api_key|private_key)\s*[:=]\s*['\"]?([^'\",\s]+)['\"]?",
    re.IGNORECASE,
)


class ConnectorSecurityError(Exception):
    """Raised when a connector operation violates security boundaries."""

    def __init__(self, message: str, code: str = "SECURITY_VIOLATION") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ReadOnlySecurityViolationError(ConnectorSecurityError):
    """Raised when an SQL query attempts data or schema modification."""

    def __init__(self, query_snippet: str) -> None:
        super().__init__(
            f"Query violates read-only connector policy: {query_snippet}",
            code="READ_ONLY_VIOLATION",
        )


class SSRFSecurityViolationError(ConnectorSecurityError):
    """Raised when a connection target attempts to access forbidden internal or cloud metadata networks."""

    def __init__(self, host: str, reason: str) -> None:
        super().__init__(
            f"Connection target '{host}' rejected by SSRF egress policy: {reason}",
            code="SSRF_VIOLATION",
        )


def validate_read_only_sql(sql: str) -> None:
    """Inspect an SQL string and raise ReadOnlySecurityViolationError if mutation tokens are detected.

    Parameters
    ----------
    sql : str
        The SQL query string to evaluate.

    Raises
    ------
    ReadOnlySecurityViolationError
        If any DDL or DML keyword is detected.
    """
    match = _MUTATION_KEYWORDS.search(sql)
    if match:
        snippet = sql[:60].strip()
        raise ReadOnlySecurityViolationError(
            f"Found forbidden token '{match.group(1)}' in '{snippet}'..."
        )


def validate_network_target(host: str, allow_private_networks: bool = False) -> None:
    """Validate a database host against SSRF and network egress boundaries.

    Parameters
    ----------
    host : str
        Hostname or IP address of the target database server.
    allow_private_networks : bool
        If True, private RFC 1918 networks are permitted (e.g. for self-hosted customer VPCs),
        but cloud metadata endpoints remain strictly forbidden.

    Raises
    ------
    SSRFSecurityViolationError
        If the target violates SSRF policies.
    """
    cleaned_host = host.strip().lower()

    # 1. Check known forbidden hostnames
    if cleaned_host in _BLOCKED_HOSTNAMES:
        raise SSRFSecurityViolationError(
            cleaned_host, "Target is a prohibited loopback or cloud metadata endpoint."
        )

    # 2. Try parsing as IP address directly
    try:
        target_ip = ip_address(cleaned_host)
    except ValueError:
        # Not a raw IP literal; hostname resolution should be validated in production network egress
        return

    # Check for link-local or cloud metadata address (169.254.169.254)
    if target_ip.is_link_local or target_ip.is_loopback:
        raise SSRFSecurityViolationError(
            cleaned_host, "Loopback and link-local addresses are strictly prohibited."
        )

    if not allow_private_networks and target_ip.is_private:
        raise SSRFSecurityViolationError(
            cleaned_host,
            "Target resolves to a private network and allow_private_networks is disabled.",
        )


def mask_sensitive_strings(text: str) -> str:
    """Mask credentials, passwords, and tokens embedded in text strings or logs."""
    if not text:
        return ""
    # Mask passwords in connection URIs (e.g. postgres://user:password@host/db -> postgres://user:***@host/db)
    masked = _SECRET_URI_REGEX.sub(r"\1***\3", text)
    # Mask password key-value assignments
    masked = _PASSWORD_FIELD_REGEX.sub(r"\1=***", masked)
    return masked


def sanitize_diagnostics(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively scrub sensitive keys from diagnostic dictionaries."""
    sanitized: dict[str, Any] = {}
    forbidden_keys = {
        "password",
        "secret",
        "token",
        "credential",
        "auth_token",
        "private_key",
        "api_key",
    }

    for key, val in data.items():
        if isinstance(val, dict):
            sanitized[key] = sanitize_diagnostics(val)
        elif any(f in key.lower() for f in forbidden_keys):
            sanitized[key] = "***"
        elif isinstance(val, str):
            sanitized[key] = mask_sensitive_strings(val)
        else:
            sanitized[key] = val

    return sanitized
