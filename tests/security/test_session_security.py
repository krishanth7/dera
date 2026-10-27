"""Security Tests for Session Lifecycle, Expiration, and Revocation.

Validates that expired, revoked, tampered, or disabled sessions are strictly rejected,
and verifies absence of plaintext session secrets in database records and audit payloads.
"""

import unittest
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

from dera_api.auth.rate_limiter import auth_rate_limiter
from dera_api.auth.tokens import hash_session_token
from dera_api.core.config import ApiSettings
from dera_api.db.base import Base
from dera_api.db.dependencies import get_db_session
from dera_api.db.engine import create_database_engine, dispose_database_engine
from dera_api.db.models.audit import SecurityAuditEvent
from dera_api.db.models.identity import User, UserSession
from dera_api.db.session import create_session_factory
from dera_api.factory import create_app
from fastapi import status
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class TestSessionSecurity(unittest.IsolatedAsyncioTestCase):
    """Test suite verifying session lifecycle security controls."""

    async def asyncSetUp(self) -> None:
        auth_rate_limiter.clear()
        self.settings = ApiSettings(
            database_url="sqlite+aiosqlite:///:memory:",
            auth_csrf_enabled=False,
        )
        self.engine = create_database_engine(self.settings)

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.session_factory = create_session_factory(self.engine)

        async def override_get_db_session() -> AsyncIterator[AsyncSession]:
            async with self.session_factory() as session:
                yield session

        self.app = create_app(self.settings)
        self.app.state.is_ready = True
        self.app.state.db_session_factory = self.session_factory
        self.app.dependency_overrides[get_db_session] = override_get_db_session

        self.client = AsyncClient(
            transport=ASGITransport(app=self.app),
            base_url="http://testserver",
        )

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await dispose_database_engine(self.engine)
        auth_rate_limiter.clear()

    async def test_expired_session_rejected(self) -> None:
        """Verify that a session past its expiration timestamp is rejected with 401."""
        res = await self.client.post(
            "/api/v1/auth/register",
            json={"email": "expired@example.com", "password": "secure-password-2026"},
        )
        token = res.cookies.get("dera_session")
        assert token is not None

        # Manually expire the session in the database
        token_hash = hash_session_token(token)
        async with self.session_factory() as session:
            stmt = select(UserSession).where(UserSession.token_hash == token_hash)
            s_result = await session.execute(stmt)
            db_sess = s_result.scalar_one()
            db_sess.expires_at = datetime.now(UTC) - timedelta(hours=1)
            await session.commit()

        # Introspect with expired session
        res_expired = await self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(res_expired.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("expired", res_expired.json()["detail"].lower())

    async def test_revoked_session_rejected(self) -> None:
        """Verify that a revoked session is rejected with 401."""
        res = await self.client.post(
            "/api/v1/auth/register",
            json={"email": "revoked@example.com", "password": "secure-password-2026"},
        )
        token = res.cookies.get("dera_session")
        assert token is not None

        # Manually revoke the session
        token_hash = hash_session_token(token)
        async with self.session_factory() as session:
            stmt = select(UserSession).where(UserSession.token_hash == token_hash)
            s_result = await session.execute(stmt)
            db_sess = s_result.scalar_one()
            db_sess.revoked_at = datetime.now(UTC)
            await session.commit()

        # Introspect with revoked session
        res_revoked = await self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(res_revoked.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("revoked", res_revoked.json()["detail"].lower())

    async def test_disabled_account_session_rejected(self) -> None:
        """Verify that disabling a user account invalidates active sessions immediately."""
        res = await self.client.post(
            "/api/v1/auth/register",
            json={"email": "disabled@example.com", "password": "secure-password-2026"},
        )
        token = res.cookies.get("dera_session")
        user_id = uuid.UUID(res.json()["user"]["id"])
        assert token is not None

        # Disable user account
        async with self.session_factory() as session:
            stmt = select(User).where(User.id == user_id)
            u_result = await session.execute(stmt)
            db_user = u_result.scalar_one()
            db_user.status = "disabled"
            await session.commit()

        # Introspect with token of disabled account
        res_disabled = await self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(res_disabled.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("disabled", res_disabled.json()["detail"].lower())

    async def test_random_tampered_token_rejected(self) -> None:
        """Verify that an arbitrary random token returns 401."""
        res = await self.client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization": "Bearer 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
            },
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    async def test_raw_token_never_persisted_in_db_or_audit(self) -> None:
        """Verify that plaintext session tokens and passwords are never stored in DB or audit logs."""
        raw_password = "super-secret-password-2026"
        res = await self.client.post(
            "/api/v1/auth/register",
            json={"email": "audit_leak_test@example.com", "password": raw_password},
        )
        raw_token = res.cookies.get("dera_session")
        assert raw_token is not None

        async with self.session_factory() as session:
            # 1. Check User table
            u_stmt = select(User).where(User.email == "audit_leak_test@example.com")
            user = (await session.execute(u_stmt)).scalar_one()
            self.assertNotEqual(user.password_hash, raw_password)
            self.assertNotIn(raw_password, user.password_hash)

            # 2. Check UserSession table
            s_stmt = select(UserSession).where(UserSession.user_id == user.id)
            sess = (await session.execute(s_stmt)).scalar_one()
            self.assertNotEqual(sess.token_hash, raw_token)
            self.assertNotIn(raw_token, sess.token_hash)

            # 3. Check SecurityAuditEvent table
            a_stmt = select(SecurityAuditEvent).where(SecurityAuditEvent.actor_user_id == user.id)
            events = (await session.execute(a_stmt)).scalars().all()
            for evt in events:
                if evt.metadata_json:
                    self.assertNotIn(raw_password, evt.metadata_json)
                    self.assertNotIn(raw_token, evt.metadata_json)


if __name__ == "__main__":
    unittest.main()
