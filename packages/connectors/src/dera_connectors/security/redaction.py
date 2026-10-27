"""DERA Connectors — Credential Redaction & Log Sanitization.

Provides deterministic masking of credentials, tokens, passwords, private keys,
and connection URIs across error messages, diagnostic dictionaries, and log records.
"""

from __future__ import annotations

import re
from typing import Any

# Sensitive regex for masking connection URIs with embedded passwords:
# e.g. postgresql://user:password@host:port/db -> postgresql://user:***@host:port/db
_SECRET_URI_REGEX = re.compile(
    r"(://[^:]+:)([^@]+)(@)",
    re.IGNORECASE,
)

# Password/token key-value assignments:
# e.g. password = 'my_secret_password' -> password=***
_PASSWORD_FIELD_REGEX = re.compile(
    r"(password|passwd|pwd|secret|token|api_key|apikey|private_key|auth_token)\s*[:=]\s*['\"]?([^'\",\s]+)['\"]?",
    re.IGNORECASE,
)

# Set of forbidden key substrings for dictionary recursive scrubbing
_FORBIDDEN_KEY_SUBSTRINGS = {
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "credential",
    "auth_token",
    "private_key",
    "api_key",
    "apikey",
    "bearer",
    "access_token",
    "refresh_token",
}


def mask_sensitive_strings(text: str) -> str:
    """Mask credentials, passwords, and tokens embedded in text strings or logs.

    Parameters
    ----------
    text : str
        Input string that may contain connection strings, passwords, or secrets.

    Returns
    -------
    str
        Sanitized string with secrets replaced by '***'.
    """
    if not text:
        return ""
    # Mask passwords in connection URIs
    masked = _SECRET_URI_REGEX.sub(r"\1***\3", text)
    # Mask key-value password assignments
    masked = _PASSWORD_FIELD_REGEX.sub(r"\1=***", masked)
    return masked


def sanitize_diagnostics(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively scrub sensitive keys from diagnostic dictionaries.

    Parameters
    ----------
    data : dict[str, Any]
        Dictionary of diagnostic metadata or connection parameters.

    Returns
    -------
    dict[str, Any]
        Sanitized dictionary with sensitive values masked with '***'.
    """
    sanitized: dict[str, Any] = {}

    for key, val in data.items():
        if isinstance(val, dict):
            sanitized[key] = sanitize_diagnostics(val)
        elif isinstance(val, list):
            sanitized[key] = [
                sanitize_diagnostics(item)
                if isinstance(item, dict)
                else mask_sensitive_strings(item)
                if isinstance(item, str)
                else item
                for item in val
            ]
        elif any(f in str(key).lower() for f in _FORBIDDEN_KEY_SUBSTRINGS):
            sanitized[key] = "***"
        elif isinstance(val, str):
            sanitized[key] = mask_sensitive_strings(val)
        else:
            sanitized[key] = val

    return sanitized


def redact_credentials(config_dict: dict[str, Any]) -> dict[str, Any]:
    """Strip or redact sensitive authentication fields from a connector config dictionary.

    Parameters
    ----------
    config_dict : dict[str, Any]
        Configuration dictionary to redact.

    Returns
    -------
    dict[str, Any]
        Redacted copy of configuration dictionary.
    """
    return sanitize_diagnostics(config_dict)


def safe_log_record(record_data: dict[str, Any]) -> dict[str, Any]:
    """Ensure a structured logging payload contains zero plaintext credentials."""
    return sanitize_diagnostics(record_data)
