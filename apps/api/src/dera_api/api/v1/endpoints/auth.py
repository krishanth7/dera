"""DERA API — Authentication Endpoints.

Provides registration, login, logout, current-user introspection, and session revocation.
Implements Secure/HttpOnly session cookies, Double-Submit CSRF defense, and rate-limiting.
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from dera_api.auth.dependencies import (
    get_current_user,
    get_current_user_and_session,
    verify_csrf,
)
from dera_api.auth.email import normalize_email
from dera_api.auth.exceptions import (
    AccountDisabledError,
    AuthRateLimitedError,
    InvalidCredentialsError,
)
from dera_api.auth.password import hash_password, verify_password
from dera_api.auth.rate_limiter import auth_rate_limiter
from dera_api.auth.tokens import (
    generate_csrf_token,
    generate_session_token,
    hash_session_token,
)
from dera_api.contracts.errors import ProblemDetail
from dera_api.core.config import ApiSettings, get_settings
from dera_api.db.dependencies import get_db_session
from dera_api.db.models.identity import User, UserSession
from dera_api.db.session import transaction_scope
from dera_api.repositories.audit import AuditRepository
from dera_api.repositories.sessions import SessionRepository
from dera_api.repositories.users import UserRepository
from dera_api.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _resolve_settings(request: Request | None = None) -> ApiSettings:
    if (
        request
        and hasattr(request, "app")
        and hasattr(request.app, "state")
        and hasattr(request.app.state, "settings")
    ):
        return request.app.state.settings
    return get_settings()


def _set_auth_cookies(
    response: Response,
    session_token: str,
    csrf_token: str,
    expires_at: datetime,
    settings: ApiSettings,
) -> None:
    """Attach Secure, HttpOnly session cookie and CSRF cookie to response."""
    max_age = int((expires_at - datetime.now(UTC)).total_seconds())

    # 1. Primary opaque session cookie (HttpOnly)
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=session_token,
        max_age=max_age,
        expires=expires_at,
        path=settings.auth_cookie_path,
        domain=settings.auth_cookie_domain,
        secure=settings.auth_cookie_secure,
        httponly=settings.auth_cookie_httponly,
        samesite=settings.auth_cookie_samesite,
    )

    # 2. Double-submit CSRF cookie (accessible to client-side scripts to copy to header)
    if settings.auth_csrf_enabled:
        response.set_cookie(
            key=settings.auth_csrf_cookie_name,
            value=csrf_token,
            max_age=max_age,
            expires=expires_at,
            path=settings.auth_cookie_path,
            domain=settings.auth_cookie_domain,
            secure=settings.auth_cookie_secure,
            httponly=False,  # Client needs to read CSRF token to echo in header
            samesite=settings.auth_cookie_samesite,
        )


def _clear_auth_cookies(response: Response, settings: ApiSettings) -> None:
    """Clear session and CSRF cookies on logout."""
    response.delete_cookie(
        key=settings.auth_cookie_name,
        path=settings.auth_cookie_path,
        domain=settings.auth_cookie_domain,
    )
    if settings.auth_csrf_enabled:
        response.delete_cookie(
            key=settings.auth_csrf_cookie_name,
            path=settings.auth_cookie_path,
            domain=settings.auth_cookie_domain,
        )


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new platform user account",
    responses={
        400: {"model": ProblemDetail, "description": "Invalid registration input or email syntax"},
        409: {"model": ProblemDetail, "description": "User email already registered"},
    },
)
async def register(
    request: Request,
    response: Response,
    payload: RegisterRequest,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthResponse:
    """Register a new user account with validated credentials and issue initial session."""
    settings = _resolve_settings(request)
    clean_email = normalize_email(payload.email)
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)

    async with transaction_scope(db_session):
        user_repo = UserRepository(db_session)
        audit_repo = AuditRepository(db_session)

        # Check existing identity
        existing = await user_repo.get_by_email(clean_email)
        if existing:
            await audit_repo.record_event(
                event_type="auth.register.duplicate_attempt",
                request_id=request_id,
                ip_address=client_ip,
                metadata={"email": clean_email},
            )
            # Raise RFC 9457 Conflict
            from starlette.exceptions import HTTPException

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email '{clean_email}' already exists.",
            )

        # Hash password and create user
        pwd_hash = hash_password(payload.password)
        user = await user_repo.create(
            email=clean_email,
            password_hash=pwd_hash,
            status="active",
        )

        # Issue initial session
        raw_token = generate_session_token()
        token_hash = hash_session_token(raw_token)
        csrf_token = generate_csrf_token()
        expires_at = datetime.now(UTC) + timedelta(seconds=settings.auth_session_lifetime_seconds)

        session_repo = SessionRepository(db_session)
        user_session = await session_repo.create_session(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=client_ip,
            user_agent=request.headers.get("User-Agent"),
        )

        # Audit event
        await audit_repo.record_event(
            event_type="auth.register.success",
            actor_user_id=user.id,
            target_type="user",
            target_id=str(user.id),
            request_id=request_id,
            ip_address=client_ip,
        )

    _set_auth_cookies(response, raw_token, csrf_token, expires_at, settings)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        session_id=user_session.id,
        csrf_token=csrf_token,
        expires_at=expires_at,
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Authenticate and establish a user session",
    responses={
        401: {"model": ProblemDetail, "description": "Invalid email or password"},
        403: {"model": ProblemDetail, "description": "Account is disabled"},
        429: {"model": ProblemDetail, "description": "Authentication rate limited"},
    },
)
async def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuthResponse:
    """Verify credentials, enforce attempt rate limiting, and issue opaque session."""
    settings = _resolve_settings(request)
    clean_email = normalize_email(payload.email)
    client_ip = request.client.host if request.client else "unknown"
    rate_limit_key = f"{client_ip}:{clean_email}"
    request_id = getattr(request.state, "request_id", None)

    # 1. Rate limiting check
    if auth_rate_limiter.is_rate_limited(
        rate_limit_key,
        max_attempts=settings.auth_rate_limit_max_attempts,
        window_seconds=settings.auth_rate_limit_window_seconds,
    ):
        raise AuthRateLimitedError()

    user_repo = UserRepository(db_session)
    audit_repo = AuditRepository(db_session)

    user = await user_repo.get_by_email(clean_email)
    if not user or not verify_password(payload.password, user.password_hash):
        auth_rate_limiter.record_failure(
            rate_limit_key,
            window_seconds=settings.auth_rate_limit_window_seconds,
        )
        async with transaction_scope(db_session):
            await audit_repo.record_event(
                event_type="auth.login.failure",
                request_id=request_id,
                ip_address=client_ip,
                metadata={"email": clean_email},
            )
        raise InvalidCredentialsError()

    if user.status != "active":
        raise AccountDisabledError()

    # Clear rate limiter upon successful authentication
    auth_rate_limiter.reset(rate_limit_key)

    async with transaction_scope(db_session):
        raw_token = generate_session_token()
        token_hash = hash_session_token(raw_token)
        csrf_token = generate_csrf_token()
        expires_at = datetime.now(UTC) + timedelta(seconds=settings.auth_session_lifetime_seconds)

        session_repo = SessionRepository(db_session)
        user_session = await session_repo.create_session(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=client_ip,
            user_agent=request.headers.get("User-Agent"),
        )

        await audit_repo.record_event(
            event_type="auth.login.success",
            actor_user_id=user.id,
            target_type="session",
            target_id=str(user_session.id),
            request_id=request_id,
            ip_address=client_ip,
        )

    _set_auth_cookies(response, raw_token, csrf_token, expires_at, settings)
    return AuthResponse(
        user=UserResponse.model_validate(user),
        session_id=user_session.id,
        csrf_token=csrf_token,
        expires_at=expires_at,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_csrf)],
    summary="Revoke the current active session and clear cookies",
    responses={
        401: {"model": ProblemDetail, "description": "Authentication required"},
        403: {"model": ProblemDetail, "description": "CSRF verification failed"},
    },
)
async def logout(
    request: Request,
    response: Response,
    current_user_and_session: Annotated[
        tuple[User, UserSession],
        Depends(get_current_user_and_session),
    ],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Revoke the calling session and instruct client to delete authentication cookies."""
    settings = _resolve_settings(request)
    user, user_session = current_user_and_session
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)

    async with transaction_scope(db_session):
        session_repo = SessionRepository(db_session)
        audit_repo = AuditRepository(db_session)

        await session_repo.revoke_session(user_session)
        await audit_repo.record_event(
            event_type="auth.logout.success",
            actor_user_id=user.id,
            target_type="session",
            target_id=str(user_session.id),
            request_id=request_id,
            ip_address=client_ip,
        )

    _clear_auth_cookies(response, settings)


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(verify_csrf)],
    summary="Revoke all active sessions for the current user across devices",
    responses={
        401: {"model": ProblemDetail, "description": "Authentication required"},
        403: {"model": ProblemDetail, "description": "CSRF verification failed"},
    },
)
async def logout_all(
    request: Request,
    response: Response,
    current_user: Annotated[User, Depends(get_current_user)],
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Revoke all sessions issued to the user for account recovery or security reset."""
    settings = _resolve_settings(request)
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)

    async with transaction_scope(db_session):
        session_repo = SessionRepository(db_session)
        audit_repo = AuditRepository(db_session)

        revoked_count = await session_repo.revoke_all_user_sessions(current_user.id)
        await audit_repo.record_event(
            event_type="auth.logout_all.success",
            actor_user_id=current_user.id,
            target_type="user",
            target_id=str(current_user.id),
            request_id=request_id,
            ip_address=client_ip,
            metadata={"revoked_sessions_count": revoked_count},
        )

    _clear_auth_cookies(response, settings)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Introspect the current authenticated user identity",
    responses={
        401: {"model": ProblemDetail, "description": "Authentication required"},
    },
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserResponse:
    """Return profile details for the authenticated user."""
    return UserResponse.model_validate(current_user)
