"""DERA Connectors — SSRF & Network Destination Security Policy.

Validates destination hosts, IP addresses, address families, and ports against SSRF,
cloud metadata endpoint access, DNS rebinding, and unauthorized private network egress.
"""

from __future__ import annotations

import socket
from collections.abc import Sequence
from ipaddress import ip_address, ip_network

from dera_connectors.security.errors import (
    DNSRebindingViolationError,
    SSRFSecurityViolationError,
)

# Prohibited hostnames (cloud metadata, loopback aliases, well-known internal discovery endpoints)
_BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata.google",
    "metadata",
    "169.254.169.254",  # AWS EC2 / GCP metadata
    "169.254.170.2",  # AWS ECS task metadata
    "instance-data",
    "wpad",
    "router",
    "gateway",
}

# Standard private, loopback, link-local, and reserved CIDR blocks
_PRIVATE_NETWORKS = [
    ip_network("0.0.0.0/8"),  # Current network
    ip_network("10.0.0.0/8"),  # RFC 1918
    ip_network("172.16.0.0/12"),  # RFC 1918
    ip_network("192.168.0.0/16"),  # RFC 1918
    ip_network("127.0.0.0/8"),  # IPv4 loopback
    ip_network("169.254.0.0/16"),  # RFC 3927 link-local / Cloud metadata
    ip_network("192.0.2.0/24"),  # TEST-NET-1
    ip_network("198.51.100.0/24"),  # TEST-NET-2
    ip_network("203.0.113.0/24"),  # TEST-NET-3
    ip_network("224.0.0.0/4"),  # Multicast
    ip_network("240.0.0.0/4"),  # Reserved / Future use
    ip_network("::1/128"),  # IPv6 loopback
    ip_network("::/128"),  # IPv6 unspecified
    ip_network("fc00::/7"),  # IPv6 unique local (ULA)
    ip_network("fe80::/10"),  # IPv6 link-local
    ip_network("ff00::/8"),  # IPv6 multicast
]

# Sensitive service ports that should not be targeted by database connectors
_PROHIBITED_PORTS = {
    21,  # FTP
    22,  # SSH
    23,  # Telnet
    25,  # SMTP
    53,  # DNS
    110,  # POP3
    135,  # RPC
    137,  # NetBIOS
    138,  # NetBIOS
    139,  # NetBIOS
    143,  # IMAP
    445,  # SMB
    2375,  # Docker daemon (unencrypted)
    2376,  # Docker daemon (TLS)
    10250,  # Kubelet API
    10255,  # Kubelet read-only
}


def validate_network_target(
    host: str,
    allow_private_networks: bool = False,
    allow_loopback: bool = False,
    port: int | None = None,
) -> None:
    """Validate a database host against SSRF and network egress boundaries.

    Parameters
    ----------
    host : str
        Hostname or IP address of target database server.
    allow_private_networks : bool
        If True, private RFC 1918 networks are permitted (for customer VPCs),
        but cloud metadata endpoints remain strictly forbidden.
    allow_loopback : bool
        If True, loopback addresses (127.0.0.1, ::1) are permitted for local testing.
    port : int | None
        Optional TCP port to validate against prohibited service ports.

    Raises
    ------
    SSRFSecurityViolationError
        If host violates SSRF policies or targets forbidden infrastructure.
    """
    cleaned_host = host.strip().lower()

    if not cleaned_host:
        raise SSRFSecurityViolationError("", "Destination hostname or IP address cannot be empty.")

    # 1. Port checks if provided
    if port is not None:
        if port < 1 or port > 65535:
            raise SSRFSecurityViolationError(
                cleaned_host, f"Port {port} is outside valid TCP port range (1-65535)."
            )
        if port in _PROHIBITED_PORTS:
            raise SSRFSecurityViolationError(
                cleaned_host, f"Port {port} is a restricted administrative service port."
            )

    # 2. Check known blocked hostnames
    if cleaned_host in _BLOCKED_HOSTNAMES:
        if allow_loopback and cleaned_host in ("localhost", "127.0.0.1", "::1"):
            return
        raise SSRFSecurityViolationError(
            cleaned_host, "Target is a prohibited loopback or cloud metadata endpoint."
        )

    # 3. Direct IP parsing check
    try:
        target_ip = ip_address(cleaned_host)
    except ValueError:
        # Hostname will be resolved in resolve_and_validate_destination
        return

    # Check loopback
    if target_ip.is_loopback:
        if not allow_loopback:
            raise SSRFSecurityViolationError(
                cleaned_host, "Loopback addresses (127.0.0.0/8, ::1) are strictly prohibited."
            )
        return

    # Check link-local / cloud metadata
    if target_ip.is_link_local:
        raise SSRFSecurityViolationError(
            cleaned_host,
            "Link-local addresses (169.254.0.0/16, fe80::/10) are strictly prohibited.",
        )

    # Check private networks
    if not allow_private_networks and target_ip.is_private:
        raise SSRFSecurityViolationError(
            cleaned_host,
            "Target resolves to a private network and allow_private_networks is disabled.",
        )


def resolve_and_validate_destination(
    host: str,
    port: int,
    allow_private_networks: bool = False,
    allow_loopback: bool = False,
    timeout_seconds: float = 3.0,
) -> list[str]:
    """Resolve a destination hostname via DNS and validate all returned IP addresses.

    Parameters
    ----------
    host : str
        Target hostname or IP string.
    port : int
        Target TCP port.
    allow_private_networks : bool
        Whether to allow private RFC 1918 IPs.
    allow_loopback : bool
        Whether to allow loopback IPs.
    timeout_seconds : float
        DNS resolution timeout.

    Returns
    -------
    list[str]
        List of validated IP address literals.

    Raises
    ------
    SSRFSecurityViolationError
        If DNS resolution fails or any resolved IP address violates security boundaries.
    """
    validate_network_target(
        host=host,
        allow_private_networks=allow_private_networks,
        allow_loopback=allow_loopback,
        port=port,
    )

    resolved_ips: list[str] = []
    try:
        addr_infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
        for _, _, _, _, sockaddr in addr_infos:
            ip_str = sockaddr[0]
            if ip_str not in resolved_ips:
                resolved_ips.append(ip_str)
    except socket.gaierror as exc:
        raise SSRFSecurityViolationError(
            host, f"DNS resolution failed for target host '{host}': {exc}"
        ) from exc

    if not resolved_ips:
        raise SSRFSecurityViolationError(
            host, f"DNS resolution returned no addresses for '{host}'."
        )

    # Validate each resolved IP address against network policy
    for ip_str in resolved_ips:
        validate_network_target(
            host=ip_str,
            allow_private_networks=allow_private_networks,
            allow_loopback=allow_loopback,
            port=port,
        )

    return resolved_ips


def verify_destination_pinning(
    host: str,
    expected_ips: Sequence[str],
    current_ip: str,
) -> None:
    """Detect and block DNS rebinding by verifying destination IP consistency.

    Parameters
    ----------
    host : str
        Original hostname.
    expected_ips : Sequence[str]
        Approved IP addresses resolved during pre-flight validation.
    current_ip : str
        Actual IP address used during socket connection.

    Raises
    ------
    DNSRebindingViolationError
        If the current connection IP was not among the pre-flight validated IPs.
    """
    if current_ip not in expected_ips:
        raise DNSRebindingViolationError(
            host=host,
            original_ip=", ".join(expected_ips),
            rebind_ip=current_ip,
        )
