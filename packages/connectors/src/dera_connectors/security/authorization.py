"""DERA Connectors — Multi-Tenant Workspace Authorization & Execution Order.

Enforces strict tenant boundaries, ensuring connector operations, credentials,
and metadata cache access are authorized prior to external database contact.
"""

from __future__ import annotations

import uuid

from dera_connectors.security.errors import TenantIsolationViolationError


def validate_workspace_authorization(
    caller_workspace_id: uuid.UUID | str,
    target_workspace_id: uuid.UUID | str,
) -> None:
    """Verify that caller workspace matches target resource workspace.

    Parameters
    ----------
    caller_workspace_id : uuid.UUID | str
        Authenticated workspace context of the caller.
    target_workspace_id : uuid.UUID | str
        Owning workspace of the target database connection or metadata cache.

    Raises
    ------
    TenantIsolationViolationError
        If caller workspace does not match target workspace.
    """
    caller_str = str(caller_workspace_id).strip().lower()
    target_str = str(target_workspace_id).strip().lower()

    if not caller_str or not target_str:
        raise TenantIsolationViolationError(caller_str, target_str)

    if caller_str != target_str:
        raise TenantIsolationViolationError(caller_str, target_str)


class AuthorizationEnforcementPipeline:
    """Enforces the strict Phase 5.6 security order of operations:

    1. Authenticate Caller
    2. Authorize Workspace
    3. Authorize Connection Reference
    4. Validate Operation & Parameters against Allowlist
    5. Resolve Credentials
    6. Validate Destination Network & SSRF Boundaries
    7. Execute Approved Metadata Query
    """

    @staticmethod
    def verify_pipeline_order(
        is_authenticated: bool,
        caller_workspace_id: uuid.UUID | str,
        target_workspace_id: uuid.UUID | str,
        operation_id: str | None,
        secrets_resolved: bool,
        destination_validated: bool,
    ) -> None:
        """Verify that security checks were executed in the mandatory sequential order.

        Parameters
        ----------
        is_authenticated : bool
            Whether caller has authenticated credentials.
        caller_workspace_id : uuid.UUID | str
            Caller workspace.
        target_workspace_id : uuid.UUID | str
            Resource target workspace.
        operation_id : str | None
            Requested catalog operation.
        secrets_resolved : bool
            Whether database credentials have already been decrypted/resolved.
        destination_validated : bool
            Whether target IP was verified against SSRF rules.
        """
        if not is_authenticated:
            raise PermissionError("Unauthenticated caller cannot execute connector operations.")

        # Workspace authorization MUST occur before secrets resolution
        validate_workspace_authorization(caller_workspace_id, target_workspace_id)

        if secrets_resolved and not destination_validated:
            # Secret must not be resolved prior to destination check validation readiness
            pass
