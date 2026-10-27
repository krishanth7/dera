"""Integration Tests for Security Audit Logging & Redaction Guarantees.

Validates that structured security audit events are captured for both allowed
and denied connector operations with zero plaintext secret exposure.
"""

import unittest
import uuid

from dera_connectors.context import ConnectorContext
from dera_connectors.security import (
    ConnectorSecurityPolicy,
    ReadOnlySecurityViolationError,
    clear_audit_events,
    get_recent_audit_events,
    log_security_audit_event,
)


class TestAuditLogging(unittest.TestCase):
    """Test suite verifying security audit logging."""

    def setUp(self) -> None:
        clear_audit_events()

    def tearDown(self) -> None:
        clear_audit_events()

    def test_log_security_audit_event_records_and_redacts(self) -> None:
        """Verify audit event records correctly and scrubs nested credentials."""
        ws = str(uuid.uuid4())
        event = log_security_audit_event(
            workspace_id=ws,
            engine="postgresql",
            operation_id="postgres.catalog.tables",
            status="ALLOW",
            duration_ms=12.5,
            details={
                "host": "postgres.prod",
                "database": "analytics",
                "password": "UltraSecretPassword123!",
                "token": "bearer-token-xyz",
            },
        )
        self.assertEqual(event.status, "ALLOW")
        self.assertEqual(event.engine, "postgresql")
        # Check details are redacted
        sanitized = event.to_dict()
        self.assertEqual(sanitized["details"]["password"], "***")
        self.assertEqual(sanitized["details"]["token"], "***")
        self.assertEqual(sanitized["details"]["host"], "postgres.prod")

        # Verify event in recent buffer
        recent = get_recent_audit_events()
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0].event_id, event.event_id)

    def test_security_policy_evaluation_logs_violations(self) -> None:
        """Verify ConnectorSecurityPolicy emits VIOLATION events when mutation occurs."""
        policy = ConnectorSecurityPolicy()
        ws_id = uuid.uuid4()
        ctx = ConnectorContext(workspace_id=ws_id)

        with self.assertRaises(ReadOnlySecurityViolationError):
            policy.evaluate_query(
                context=ctx,
                engine="postgresql",
                operation_id="postgres.catalog.tables",
                sql="DROP TABLE users;",
            )

        events = get_recent_audit_events()
        self.assertGreaterEqual(len(events), 1)
        violation_event = [e for e in events if e.status == "VIOLATION"][0]
        self.assertEqual(violation_event.operation_id, "postgres.catalog.tables")
        self.assertIn("DROP", str(violation_event.details))


if __name__ == "__main__":
    unittest.main()
