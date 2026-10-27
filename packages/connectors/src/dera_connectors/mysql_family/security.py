"""DERA MySQL-Family Connectors — Network, TLS & Session Security.

Provides SSRF network boundary enforcement, TLS SSLContext generation, and
read-only session parameter configuration for MySQL and MariaDB adapters.
"""

from __future__ import annotations

import ssl

from dera_connectors.configuration import TLSSettings
from dera_connectors.errors import (
    ConnectorInvalidConfigurationError,
    ConnectorSecurityViolationError,
)
from dera_connectors.security import (
    SSRFSecurityViolationError,
    validate_network_target,
)


def validate_mysql_destination(
    host: str,
    port: int,
    allow_loopback: bool = False,
    allow_private_networks: bool = True,
) -> None:
    """Validate host and port against network security boundaries and SSRF rules.

    Parameters
    ----------
    host : str
        Target MySQL or MariaDB hostname or IP address.
    port : int
        Target TCP port.
    allow_loopback : bool
        Whether loopback (127.0.0.1) is permitted (for local/testing workloads).
    allow_private_networks : bool
        Whether RFC 1918 private IPs are permitted.

    Raises
    ------
    ConnectorSecurityViolationError
        If target host resolves to a prohibited network or cloud metadata service.
    """
    if port < 1 or port > 65535:
        raise ConnectorSecurityViolationError(
            f"Port {port} is outside valid TCP port range (1-65535)."
        )

    cleaned_host = host.strip().lower()
    if cleaned_host in ("127.0.0.1", "localhost", "::1"):
        if not allow_loopback:
            raise ConnectorSecurityViolationError(
                f"Loopback destination '{cleaned_host}' is prohibited without explicit authorization."
            )
        return

    try:
        validate_network_target(
            host=cleaned_host,
            allow_private_networks=allow_private_networks,
        )
    except SSRFSecurityViolationError as exc:
        raise ConnectorSecurityViolationError(str(exc)) from exc


def build_mysql_ssl_context(tls_settings: TLSSettings) -> ssl.SSLContext | None:
    """Build a hardened Python ssl.SSLContext from DERA TLSSettings.

    Parameters
    ----------
    tls_settings : TLSSettings
        TLS mode and certificate configuration.

    Returns
    -------
    ssl.SSLContext | None
        Configured SSLContext, or None if ssl_mode is 'disable'.
    """
    mode = tls_settings.ssl_mode.lower()
    if mode in ("disable", "none", "off"):
        return None

    # Modern TLS 1.2+ minimum
    context = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
    context.minimum_version = ssl.TLSVersion.TLSv1_2

    # Load custom CA certificate if supplied
    if tls_settings.ca_cert_path:
        try:
            context.load_verify_locations(cafile=tls_settings.ca_cert_path)
        except Exception as exc:
            raise ConnectorInvalidConfigurationError(
                f"Failed to load CA certificate bundle at '{tls_settings.ca_cert_path}': {exc}"
            ) from exc

    # Load client certificate & key for mTLS
    if tls_settings.client_cert_path and tls_settings.client_key_path:
        try:
            context.load_cert_chain(
                certfile=tls_settings.client_cert_path,
                keyfile=tls_settings.client_key_path,
            )
        except Exception as exc:
            raise ConnectorInvalidConfigurationError(
                f"Failed to load client certificate chain for mTLS: {exc}"
            ) from exc

    if mode in ("require", "required"):
        # Encrypt transport without strict certificate verification
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    elif mode in ("verify_ca", "verify-ca"):
        context.check_hostname = False
        context.verify_mode = ssl.CERT_REQUIRED
    elif mode in ("verify_full", "verify-full"):
        context.check_hostname = bool(tls_settings.verify_hostname)
        context.verify_mode = ssl.CERT_REQUIRED
    else:
        raise ConnectorInvalidConfigurationError(
            f"Unsupported TLS ssl_mode: '{tls_settings.ssl_mode}'"
        )

    return context


def build_mysql_read_only_session_sql(
    timeout_seconds: float = 30.0,
    timeout_ms: int | None = None,
) -> list[str]:
    """Generate session-level read-only initialization statements.

    Parameters
    ----------
    timeout_seconds : float
        Query execution deadline in seconds (default 30.0).
    timeout_ms : int | None
        Query execution deadline in milliseconds. Overrides timeout_seconds if provided.

    Returns
    -------
    list[str]
        List of SQL statements to execute upon connection establishment.
    """
    effective_ms = timeout_ms if timeout_ms is not None else max(int(timeout_seconds * 1000), 1000)
    effective_sec = max(effective_ms / 1000.0, 1.0)
    return [
        "SET SESSION TRANSACTION READ ONLY;",
        f"SET SESSION max_execution_time = {effective_ms};",
        f"SET SESSION max_statement_time = {effective_sec};",
        "SET SESSION sql_safe_updates = 1;",
    ]
