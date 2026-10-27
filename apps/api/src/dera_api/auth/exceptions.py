"""DERA Auth — Domain Authentication & Access Control Exceptions.

Defines typed domain exceptions for authentication failures, session lifecycle,
and workspace authorization denials mapped to RFC 9457 error contracts.
"""

from dera_api.contracts.errors import ErrorCode
from dera_api.core.exceptions import DeraError


class AuthDomainException(DeraError):
    """Base class for all authentication and authorization domain errors."""

    def __init__(self, message: str, code: ErrorCode, status_code: int = 401) -> None:
        super().__init__(message=message, code=code, status_code=status_code, detail=message)


class AuthenticationRequiredError(AuthDomainException):
    """Raised when an unauthenticated request attempts to access a protected endpoint."""

    def __init__(self, message: str = "Authentication credentials are required.") -> None:
        super().__init__(message, ErrorCode.AUTHENTICATION_REQUIRED, status_code=401)


class InvalidCredentialsError(AuthDomainException):
    """Raised when login fails due to incorrect email or password."""

    def __init__(self, message: str = "Invalid email or password.") -> None:
        super().__init__(message, ErrorCode.INVALID_CREDENTIALS, status_code=401)


class SessionExpiredError(AuthDomainException):
    """Raised when a session's expiration timestamp has passed."""

    def __init__(self, message: str = "Your session has expired. Please sign in again.") -> None:
        super().__init__(message, ErrorCode.SESSION_EXPIRED, status_code=401)


class SessionRevokedError(AuthDomainException):
    """Raised when a previously valid session was revoked (logged out)."""

    def __init__(self, message: str = "Your session has been revoked.") -> None:
        super().__init__(message, ErrorCode.SESSION_REVOKED, status_code=401)


class AccountDisabledError(AuthDomainException):
    """Raised when an account's status is not active (disabled or suspended)."""

    def __init__(self, message: str = "This user account is disabled.") -> None:
        super().__init__(message, ErrorCode.ACCOUNT_DISABLED, status_code=403)


class PermissionDeniedError(AuthDomainException):
    """Raised when an authenticated user lacks the required workspace permission."""

    def __init__(self, message: str = "You do not have permission to perform this action.") -> None:
        super().__init__(message, ErrorCode.PERMISSION_DENIED, status_code=403)


class WorkspaceAccessDeniedError(AuthDomainException):
    """Raised when an authenticated user is not an active member of the requested workspace."""

    def __init__(self, message: str = "Access to the requested workspace was denied.") -> None:
        super().__init__(message, ErrorCode.WORKSPACE_ACCESS_DENIED, status_code=403)


class MembershipNotFoundError(AuthDomainException):
    """Raised when a specific user membership is not found within a workspace."""

    def __init__(self, message: str = "Workspace membership was not found.") -> None:
        super().__init__(message, ErrorCode.MEMBERSHIP_NOT_FOUND, status_code=404)


class AuthRateLimitedError(AuthDomainException):
    """Raised when excessive authentication attempts trigger rate limiting."""

    def __init__(
        self, message: str = "Too many authentication attempts. Please try again later."
    ) -> None:
        super().__init__(message, ErrorCode.AUTH_RATE_LIMITED, status_code=429)


class CsrfValidationError(AuthDomainException):
    """Raised when a state-changing cookie-authenticated request fails CSRF verification."""

    def __init__(
        self, message: str = "CSRF verification failed. Missing or invalid CSRF token."
    ) -> None:
        super().__init__(message, ErrorCode.CSRF_FAILED, status_code=403)
