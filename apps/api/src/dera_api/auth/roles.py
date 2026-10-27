"""DERA Auth — Roles and Permission Taxonomy.

Defines the centralized role and permission registry for workspace tenancy.
All permissions are deterministic strings mapped to explicit WorkspaceRole levels.
"""

from enum import StrEnum


class WorkspaceRole(StrEnum):
    """Authoritative workspace membership roles ordered by privilege level."""

    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class Permission(StrEnum):
    """Centralized machine-readable permission tokens."""

    # Workspace operations
    WORKSPACE_READ = "workspace:read"
    WORKSPACE_UPDATE = "workspace:update"
    WORKSPACE_DELETE = "workspace:delete"

    # Member operations
    MEMBER_READ = "member:read"
    MEMBER_INVITE = "member:invite"
    MEMBER_UPDATE_ROLE = "member:update_role"
    MEMBER_REMOVE = "member:remove"

    # Audit log operations
    AUDIT_READ = "audit:read"

    # Background worker & job orchestration operations (Phase 4.5)
    JOB_CREATE = "job:create"
    JOB_READ = "job:read"
    JOB_CANCEL = "job:cancel"
    JOB_RETRY = "job:retry"
    JOB_ADMIN = "job:admin"

    # Reserved connector operations (Phase 5+)
    CONNECTION_READ = "connection:read"
    CONNECTION_CREATE = "connection:create"
    CONNECTION_UPDATE = "connection:update"
    CONNECTION_DELETE = "connection:delete"
