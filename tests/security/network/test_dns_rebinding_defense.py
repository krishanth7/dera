"""Tests for DNS Rebinding Defense & Destination Pinning.

Validates that destination IP changes between pre-flight validation and connection
are detected and blocked.
"""

import unittest

from dera_connectors.security import (
    DNSRebindingViolationError,
    verify_destination_pinning,
)


class TestDNSRebindingDefense(unittest.TestCase):
    """Test suite verifying DNS rebinding countermeasures."""

    def test_pinned_destination_passes(self) -> None:
        """Verify connection to an approved pre-flight resolved IP succeeds."""
        approved = ["93.184.216.34", "93.184.216.35"]
        # Connection uses one of the approved IPs
        try:
            verify_destination_pinning(
                host="example.com",
                expected_ips=approved,
                current_ip="93.184.216.34",
            )
        except DNSRebindingViolationError:
            self.fail("Valid pinned IP was falsely rejected.")

    def test_rebound_ip_rejected(self) -> None:
        """Verify connection to an IP that was not in the approved pre-flight list is rejected."""
        approved = ["93.184.216.34"]
        # Attacker shifts DNS to point to 169.254.169.254 or 127.0.0.1
        with self.assertRaises(DNSRebindingViolationError) as ctx:
            verify_destination_pinning(
                host="attacker-controlled.net",
                expected_ips=approved,
                current_ip="169.254.169.254",
            )
        self.assertIn("attacker-controlled.net", ctx.exception.message)
        self.assertEqual(ctx.exception.details["rebind_ip"], "169.254.169.254")


if __name__ == "__main__":
    unittest.main()
