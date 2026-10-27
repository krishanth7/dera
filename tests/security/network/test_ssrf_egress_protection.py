"""Tests for SSRF Egress Boundary & Port Enforcement.

Validates that database connectors reject loopback interfaces, cloud metadata endpoints,
private network ranges (when disallowed), and restricted administrative service ports.
"""

import unittest

from dera_connectors.security import (
    SSRFSecurityViolationError,
    validate_network_target,
)


class TestSSRFProtection(unittest.TestCase):
    """Test suite verifying SSRF boundary controls."""

    def test_cloud_metadata_endpoints_blocked_unconditionally(self) -> None:
        """Verify AWS, GCP, and Azure metadata endpoints are blocked even if allow_private_networks=True."""
        blocked = [
            "169.254.169.254",  # AWS/GCP instance metadata
            "169.254.170.2",  # AWS ECS task metadata
            "metadata.google.internal",
            "metadata.google",
            "metadata",
            "instance-data",
        ]
        for host in blocked:
            with self.assertRaises(
                SSRFSecurityViolationError,
                msg=f"Metadata endpoint '{host}' was not blocked.",
            ):
                validate_network_target(host, allow_private_networks=True, allow_loopback=True)

    def test_loopback_interfaces_blocked_by_default(self) -> None:
        """Verify loopback addresses are blocked unless allow_loopback=True."""
        loopbacks = ["127.0.0.1", "127.0.1.1", "localhost", "::1"]
        for host in loopbacks:
            with self.assertRaises(
                SSRFSecurityViolationError,
                msg=f"Loopback '{host}' was not blocked.",
            ):
                validate_network_target(host, allow_loopback=False, allow_private_networks=False)

        # Permitted when explicit allow_loopback=True
        for host in loopbacks:
            try:
                validate_network_target(host, allow_loopback=True, allow_private_networks=False)
            except SSRFSecurityViolationError:
                self.fail(f"Loopback '{host}' failed when allow_loopback=True.")

    def test_private_networks_blocked_when_disallowed(self) -> None:
        """Verify RFC 1918 and ULA addresses are blocked when allow_private_networks=False."""
        privates = [
            "10.0.0.1",
            "10.254.0.1",
            "172.16.0.1",
            "172.31.255.255",
            "192.168.0.1",
            "192.168.1.254",
            "fc00::1",
            "fe80::1",  # Link-local
        ]
        for ip in privates:
            with self.assertRaises(
                SSRFSecurityViolationError,
                msg=f"Private IP '{ip}' was not blocked.",
            ):
                validate_network_target(ip, allow_private_networks=False)

    def test_public_ips_permitted(self) -> None:
        """Verify routable public IP addresses pass validation."""
        public_ips = ["8.8.8.8", "1.1.1.1", "93.184.216.34", "2606:4700:4700::1111"]
        for ip in public_ips:
            try:
                validate_network_target(ip, allow_private_networks=False)
            except SSRFSecurityViolationError:
                self.fail(f"Public IP '{ip}' was incorrectly rejected.")

    def test_prohibited_service_ports_blocked(self) -> None:
        """Verify connecting to non-database administrative ports is blocked."""
        bad_ports = [21, 22, 23, 25, 53, 445, 2375, 2376, 10250]
        for port in bad_ports:
            with self.assertRaises(
                SSRFSecurityViolationError,
                msg=f"Restricted port {port} was not blocked.",
            ):
                validate_network_target("8.8.8.8", port=port)

        # Standard database ports pass
        valid_ports = [5432, 3306, 3307, 6543, 5433, 15432]
        for port in valid_ports:
            try:
                validate_network_target("8.8.8.8", port=port)
            except SSRFSecurityViolationError:
                self.fail(f"Valid database port {port} was falsely rejected.")

    def test_invalid_port_range_blocked(self) -> None:
        """Verify out of range ports (<1 or >65535) are blocked."""
        for port in [0, -1, 65536, 99999]:
            with self.assertRaises(SSRFSecurityViolationError):
                validate_network_target("8.8.8.8", port=port)


if __name__ == "__main__":
    unittest.main()
