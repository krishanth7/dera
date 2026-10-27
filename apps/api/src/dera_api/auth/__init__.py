"""DERA Auth Package.

Provides authentication, session management, password hashing, roles,
and authorization policies for the DERA platform backend.
"""

from dera_api.auth.email import EmailValidationError, normalize_email
from dera_api.auth.exceptions import (
    AccountDisabledError,
    AuthDomainException,
    AuthenticationRequiredError,
    AuthRateLimitedError,
    CsrfValidationError,
    InvalidCredentialsError,
    MembershipNotFoundError,
    PermissionDeniedError,
    SessionExpiredError,
    SessionRevokedError,
    WorkspaceAccessDeniedError,
)
from dera_api.auth.password import (
    PasswordPolicyError,
    hash_password,
    validate_password_complexity,
    verify_password,
)
from dera_api.auth.policies import (
    ROLE_PERMISSIONS,
    PolicyViolationError,
    has_permission,
    validate_owner_removal,
    validate_role_transition,
)
from dera_api.auth.roles import Permission, WorkspaceRole
from dera_api.auth.tokens import (
    constant_time_compare,
    generate_csrf_token,
    generate_session_token,
    hash_session_token,
)

__all__ = [
    "ROLE_PERMISSIONS",
    "AccountDisabledError",
    "AuthDomainException",
    "AuthRateLimitedError",
    "AuthenticationRequiredError",
    "CsrfValidationError",
    "EmailValidationError",
    "InvalidCredentialsError",
    "MembershipNotFoundError",
    "PasswordPolicyError",
    "Permission",
    "PermissionDeniedError",
    "PolicyViolationError",
    "SessionExpiredError",
    "SessionRevokedError",
    "WorkspaceAccessDeniedError",
    "WorkspaceRole",
    "constant_time_compare",
    "generate_csrf_token",
    "generate_session_token",
    "has_permission",
    "hash_password",
    "hash_session_token",
    "normalize_email",
    "validate_owner_removal",
    "validate_password_complexity",
    "validate_role_transition",
    "verify_password",
]
