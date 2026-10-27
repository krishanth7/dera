"""Tests for Centralized RBAC Policies and Hierarchy Safeguards.

Validates default-deny policy, role-to-permission mapping, privilege escalation checks,
and safeguards against leaving a workspace ownerless.
"""

import unittest

from dera_api.auth.policies import (
    PolicyViolationError,
    has_permission,
    validate_owner_removal,
    validate_role_transition,
)
from dera_api.auth.roles import Permission, WorkspaceRole


class TestRbacPolicies(unittest.TestCase):
    """Test suite for role permissions and administrative constraints."""

    def test_default_deny(self) -> None:
        """Verify that unknown roles, None, or unrecognized permissions return False."""
        self.assertFalse(has_permission(None, Permission.WORKSPACE_READ))
        self.assertFalse(has_permission("invalid-role", Permission.WORKSPACE_READ))
        self.assertFalse(has_permission(WorkspaceRole.VIEWER, "invalid:permission"))

    def test_viewer_permissions(self) -> None:
        """Verify Viewer role has read-only access and no mutation permissions."""
        self.assertTrue(has_permission(WorkspaceRole.VIEWER, Permission.WORKSPACE_READ))
        self.assertTrue(has_permission(WorkspaceRole.VIEWER, Permission.MEMBER_READ))
        self.assertTrue(has_permission(WorkspaceRole.VIEWER, Permission.CONNECTION_READ))

        self.assertFalse(has_permission(WorkspaceRole.VIEWER, Permission.WORKSPACE_UPDATE))
        self.assertFalse(has_permission(WorkspaceRole.VIEWER, Permission.WORKSPACE_DELETE))
        self.assertFalse(has_permission(WorkspaceRole.VIEWER, Permission.MEMBER_INVITE))
        self.assertFalse(has_permission(WorkspaceRole.VIEWER, Permission.MEMBER_REMOVE))

    def test_editor_permissions(self) -> None:
        """Verify Editor role includes connector mutation but no workspace admin."""
        self.assertTrue(has_permission(WorkspaceRole.EDITOR, Permission.WORKSPACE_READ))
        self.assertTrue(has_permission(WorkspaceRole.EDITOR, Permission.CONNECTION_CREATE))
        self.assertTrue(has_permission(WorkspaceRole.EDITOR, Permission.CONNECTION_UPDATE))

        self.assertFalse(has_permission(WorkspaceRole.EDITOR, Permission.WORKSPACE_UPDATE))
        self.assertFalse(has_permission(WorkspaceRole.EDITOR, Permission.WORKSPACE_DELETE))
        self.assertFalse(has_permission(WorkspaceRole.EDITOR, Permission.MEMBER_INVITE))

    def test_admin_permissions(self) -> None:
        """Verify Admin role includes member management and workspace update but not delete."""
        self.assertTrue(has_permission(WorkspaceRole.ADMIN, Permission.WORKSPACE_UPDATE))
        self.assertTrue(has_permission(WorkspaceRole.ADMIN, Permission.MEMBER_INVITE))
        self.assertTrue(has_permission(WorkspaceRole.ADMIN, Permission.MEMBER_UPDATE_ROLE))
        self.assertTrue(has_permission(WorkspaceRole.ADMIN, Permission.MEMBER_REMOVE))
        self.assertTrue(has_permission(WorkspaceRole.ADMIN, Permission.AUDIT_READ))

        self.assertFalse(has_permission(WorkspaceRole.ADMIN, Permission.WORKSPACE_DELETE))

    def test_owner_permissions(self) -> None:
        """Verify Owner role possesses all permissions including workspace deletion."""
        for perm in Permission:
            self.assertTrue(
                has_permission(WorkspaceRole.OWNER, perm),
                f"Owner must have permission '{perm}'",
            )

    def test_role_transition_rules(self) -> None:
        """Verify hierarchy rules preventing unauthorized role assignment."""
        # Viewer cannot modify roles
        with self.assertRaises(PolicyViolationError):
            validate_role_transition(
                WorkspaceRole.VIEWER, WorkspaceRole.VIEWER, WorkspaceRole.EDITOR
            )

        # Editor cannot modify roles
        with self.assertRaises(PolicyViolationError):
            validate_role_transition(
                WorkspaceRole.EDITOR, WorkspaceRole.VIEWER, WorkspaceRole.EDITOR
            )

        # Admin cannot promote anyone to Owner
        with self.assertRaises(PolicyViolationError):
            validate_role_transition(WorkspaceRole.ADMIN, WorkspaceRole.EDITOR, WorkspaceRole.OWNER)

        # Admin cannot demote an Owner
        with self.assertRaises(PolicyViolationError):
            validate_role_transition(WorkspaceRole.ADMIN, WorkspaceRole.OWNER, WorkspaceRole.VIEWER)

        # Admin can promote Viewer to Editor
        validate_role_transition(WorkspaceRole.ADMIN, WorkspaceRole.VIEWER, WorkspaceRole.EDITOR)

        # Owner can assign any role including Owner
        validate_role_transition(WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.OWNER)

    def test_owner_removal_safeguard(self) -> None:
        """Verify prevention of removing or demoting the last remaining active owner."""
        # Only 1 owner left: must raise error
        with self.assertRaises(PolicyViolationError):
            validate_owner_removal(active_owner_count=1)

        with self.assertRaises(PolicyViolationError):
            validate_owner_removal(active_owner_count=0)

        # 2 owners present: removal allowed
        validate_owner_removal(active_owner_count=2)


if __name__ == "__main__":
    unittest.main()
