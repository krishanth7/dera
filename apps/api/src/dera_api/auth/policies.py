"""DERA Auth — Centralized Authorization Policies and Role Permissions.

Implements default-deny authorization, deterministic role-to-permission resolution,
and administrative safety safeguards (e.g., preventing ownerless workspaces).
"""

from dera_api.auth.roles import Permission, WorkspaceRole

# Explicit role permission mappings
ROLE_PERMISSIONS: dict[WorkspaceRole, frozenset[Permission]] = {
    WorkspaceRole.VIEWER: frozenset(
        {
            Permission.WORKSPACE_READ,
            Permission.MEMBER_READ,
            Permission.JOB_READ,
            Permission.CONNECTION_READ,
            Permission.SCHEMA_READ,
            Permission.SNAPSHOT_READ,
            Permission.EXPORT_READ,
        }
    ),
    WorkspaceRole.EDITOR: frozenset(
        {
            Permission.WORKSPACE_READ,
            Permission.MEMBER_READ,
            Permission.JOB_CREATE,
            Permission.JOB_READ,
            Permission.JOB_CANCEL,
            Permission.JOB_RETRY,
            Permission.CONNECTION_READ,
            Permission.CONNECTION_CREATE,
            Permission.CONNECTION_UPDATE,
            Permission.CONNECTION_DELETE,
            Permission.SCHEMA_READ,
            Permission.SNAPSHOT_CREATE,
            Permission.SNAPSHOT_READ,
            Permission.SNAPSHOT_VERIFY,
            Permission.EXPORT_CREATE,
            Permission.EXPORT_READ,
        }
    ),
    WorkspaceRole.ADMIN: frozenset(
        {
            Permission.WORKSPACE_READ,
            Permission.WORKSPACE_UPDATE,
            Permission.MEMBER_READ,
            Permission.MEMBER_INVITE,
            Permission.MEMBER_UPDATE_ROLE,
            Permission.MEMBER_REMOVE,
            Permission.AUDIT_READ,
            Permission.JOB_CREATE,
            Permission.JOB_READ,
            Permission.JOB_CANCEL,
            Permission.JOB_RETRY,
            Permission.JOB_ADMIN,
            Permission.CONNECTION_READ,
            Permission.CONNECTION_CREATE,
            Permission.CONNECTION_UPDATE,
            Permission.CONNECTION_DELETE,
            Permission.SCHEMA_READ,
            Permission.SNAPSHOT_CREATE,
            Permission.SNAPSHOT_READ,
            Permission.SNAPSHOT_VERIFY,
            Permission.EXPORT_CREATE,
            Permission.EXPORT_READ,
        }
    ),
    WorkspaceRole.OWNER: frozenset(
        {
            Permission.WORKSPACE_READ,
            Permission.WORKSPACE_UPDATE,
            Permission.WORKSPACE_DELETE,
            Permission.MEMBER_READ,
            Permission.MEMBER_INVITE,
            Permission.MEMBER_UPDATE_ROLE,
            Permission.MEMBER_REMOVE,
            Permission.AUDIT_READ,
            Permission.JOB_CREATE,
            Permission.JOB_READ,
            Permission.JOB_CANCEL,
            Permission.JOB_RETRY,
            Permission.JOB_ADMIN,
            Permission.CONNECTION_READ,
            Permission.CONNECTION_CREATE,
            Permission.CONNECTION_UPDATE,
            Permission.CONNECTION_DELETE,
            Permission.SCHEMA_READ,
            Permission.SNAPSHOT_CREATE,
            Permission.SNAPSHOT_READ,
            Permission.SNAPSHOT_VERIFY,
            Permission.EXPORT_CREATE,
            Permission.EXPORT_READ,
        }
    ),
}

# Role hierarchy levels for transition checks
_ROLE_RANK: dict[WorkspaceRole, int] = {
    WorkspaceRole.VIEWER: 10,
    WorkspaceRole.EDITOR: 20,
    WorkspaceRole.ADMIN: 30,
    WorkspaceRole.OWNER: 40,
}


class PolicyViolationError(ValueError):
    """Raised when an administrative action violates workspace role safety rules."""


def has_permission(
    role: str | WorkspaceRole | None,
    permission: str | Permission,
) -> bool:
    """Evaluate whether an assigned role possesses the requested permission.

    Default-deny policy: returns False if role is None, unrecognized, or lacks permission.
    """
    if role is None:
        return False

    try:
        ws_role = WorkspaceRole(str(role).lower())
    except ValueError:
        return False

    try:
        req_perm = Permission(str(permission))
    except ValueError:
        return False

    allowed_perms = ROLE_PERMISSIONS.get(ws_role, frozenset())
    return req_perm in allowed_perms


def validate_role_transition(
    actor_role: WorkspaceRole,
    current_target_role: WorkspaceRole,
    new_target_role: WorkspaceRole,
) -> None:
    """Validate that an actor possesses sufficient privilege to modify a member's role.

    Rules:
    - Actor must have ADMIN or OWNER role.
    - ADMIN cannot modify an OWNER's role.
    - ADMIN cannot elevate any user to OWNER.
    - ADMIN cannot assign a role with equal or higher rank than their own.
    - Only an OWNER can transfer or assign the OWNER role.
    """
    actor_rank = _ROLE_RANK.get(actor_role, 0)
    new_rank = _ROLE_RANK.get(new_target_role, 0)

    if actor_rank < _ROLE_RANK[WorkspaceRole.ADMIN]:
        raise PolicyViolationError("Only workspace administrators or owners can modify roles.")

    if actor_role != WorkspaceRole.OWNER:
        # Non-owner cannot modify an owner
        if current_target_role == WorkspaceRole.OWNER:
            raise PolicyViolationError("Cannot modify the role of a workspace owner.")
        # Non-owner cannot promote to owner
        if new_target_role == WorkspaceRole.OWNER:
            raise PolicyViolationError("Only workspace owners can promote a member to owner.")
        # Non-owner cannot promote to or above their own rank
        if new_rank >= actor_rank:
            raise PolicyViolationError("Cannot assign a role equal to or higher than your own.")


def validate_owner_removal(active_owner_count: int) -> None:
    """Ensure that a workspace always retains at least one active owner.

    Prevents ownerless workspaces.
    """
    if active_owner_count <= 1:
        raise PolicyViolationError(
            "Cannot remove or demote the last remaining owner of a workspace. Transfer ownership first."
        )
