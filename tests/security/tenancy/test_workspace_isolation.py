"""Tests for Multi-Tenant Workspace Isolation.

Validates that connector operations, configurations, and metadata caches cannot be
accessed across distinct workspace contexts.
"""

import unittest
import uuid

from dera_connectors.security import (
    AuthorizationEnforcementPipeline,
    TenantIsolationViolationError,
    validate_workspace_authorization,
)


class TestWorkspaceIsolation(unittest.TestCase):
    """Test suite verifying tenant separation invariants."""

    def test_same_workspace_authorized(self) -> None:
        """Verify access is granted when caller and target workspace IDs match."""
        ws_id = uuid.uuid4()
        try:
            validate_workspace_authorization(ws_id, ws_id)
            validate_workspace_authorization(str(ws_id), str(ws_id))
        except TenantIsolationViolationError:
            self.fail("Matching workspace IDs were incorrectly rejected.")

    def test_cross_workspace_access_denied(self) -> None:
        """Verify access is denied when caller attempts to access another workspace."""
        ws_caller = uuid.uuid4()
        ws_target = uuid.uuid4()

        with self.assertRaises(TenantIsolationViolationError) as ctx:
            validate_workspace_authorization(ws_caller, ws_target)

        self.assertIn(str(ws_caller), ctx.exception.message)
        self.assertIn(str(ws_target), ctx.exception.message)
        self.assertEqual(ctx.exception.details["caller_workspace_id"], str(ws_caller))
        self.assertEqual(ctx.exception.details["target_workspace_id"], str(ws_target))

    def test_empty_workspace_id_denied(self) -> None:
        """Verify empty or missing workspace IDs fail closed."""
        with self.assertRaises(TenantIsolationViolationError):
            validate_workspace_authorization("", str(uuid.uuid4()))

        with self.assertRaises(TenantIsolationViolationError):
            validate_workspace_authorization(str(uuid.uuid4()), "")

    def test_pipeline_order_enforces_authentication_and_tenancy_first(self) -> None:
        """Verify pipeline enforces authentication before workspace access."""
        ws = uuid.uuid4()
        with self.assertRaises(PermissionError):
            AuthorizationEnforcementPipeline.verify_pipeline_order(
                is_authenticated=False,
                caller_workspace_id=ws,
                target_workspace_id=ws,
                operation_id="postgres.catalog.tables",
                secrets_resolved=False,
                destination_validated=False,
            )


if __name__ == "__main__":
    unittest.main()
