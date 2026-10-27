"""Integration Tests for Authentication Endpoints.

Validates registration, login, logout, current-user introspection, session revocation,
cookie handling, CSRF defenses, and rate-limiting.
"""

import unittest
from collections.abc import AsyncIterator

from dera_api.auth.rate_limiter import auth_rate_limiter
from dera_api.core.config import ApiSettings
from dera_api.db.base import Base
from dera_api.db.dependencies import get_db_session
from dera_api.db.engine import create_database_engine, dispose_database_engine
from dera_api.db.session import create_session_factory
from dera_api.factory import create_app
from fastapi import status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestAuthEndpoints(unittest.IsolatedAsyncioTestCase):
    """Integration test suite for authentication endpoints."""

    async def asyncSetUp(self) -> None:
        auth_rate_limiter.clear()
        self.settings = ApiSettings(
            database_url="sqlite+aiosqlite:///:memory:",
            auth_csrf_enabled=True,
            auth_rate_limit_max_attempts=3,
            auth_rate_limit_window_seconds=60,
        )
        self.engine = create_database_engine(self.settings)

        # Create all tables in SQLite memory
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

    async def test_register_success(self) -> None:
        """Verify successful user registration returns 201 and sets session cookie."""
        res = await self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "Engineer@Example.COM",
                "password": "correct-horse-battery-staple-2026",
            },
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.json()
        self.assertEqual(data["user"]["email"], "engineer@example.com")
        self.assertEqual(data["user"]["status"], "active")
        self.assertIn("session_id", data)
        self.assertIn("csrf_token", data)

        # Verify session cookie was set
        cookies = res.cookies
        self.assertIn("dera_session", cookies)
        self.assertIn("dera_csrf", cookies)

    async def test_register_duplicate_conflict(self) -> None:
        """Verify registering an existing email returns 409 Conflict."""
        payload = {
            "email": "duplicate@example.com",
            "password": "correct-horse-battery-staple-2026",
        }
        res1 = await self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        res2 = await self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(res2.status_code, status.HTTP_409_CONFLICT)
        data = res2.json()
        self.assertIn("already exists", data["detail"])

    async def test_register_invalid_password(self) -> None:
        """Verify password policy violation returns validation error."""
        res = await self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "short",
            },
        )
        self.assertEqual(res.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    async def test_login_success_and_me_introspection(self) -> None:
        """Verify login succeeds and session introspects correctly via /api/v1/auth/me."""
        reg_payload = {
            "email": "login_test@example.com",
            "password": "super-secure-password-2026",
        }
        await self.client.post("/api/v1/auth/register", json=reg_payload)

        # Clear client cookies to test fresh login
        self.client.cookies.clear()

        # Login
        login_res = await self.client.post(
            "/api/v1/auth/login",
            json=reg_payload,
        )
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        login_data = login_res.json()
        self.assertEqual(login_data["user"]["email"], reg_payload["email"])
        raw_session_cookie = login_res.cookies.get("dera_session")
        self.assertIsNotNone(raw_session_cookie)

        # Introspect with session cookie
        me_res = await self.client.get("/api/v1/auth/me")
        self.assertEqual(me_res.status_code, status.HTTP_200_OK)
        me_data = me_res.json()
        self.assertEqual(me_data["email"], "login_test@example.com")

        # Introspect with explicit Authorization: Bearer header
        self.client.cookies.clear()
        assert raw_session_cookie is not None
        bearer_res = await self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {raw_session_cookie}"},
        )
        self.assertEqual(bearer_res.status_code, status.HTTP_200_OK)
        self.assertEqual(bearer_res.json()["email"], "login_test@example.com")

    async def test_login_invalid_credentials_returns_generic_401(self) -> None:
        """Verify invalid credentials return generic 401 without user enumeration."""
        res = await self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrong-password-1234",
            },
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        data = res.json()
        self.assertEqual(data["detail"], "Invalid email or password.")

    async def test_login_rate_limiting(self) -> None:
        """Verify that excessive failed logins trigger 429 Rate Limited."""
        payload = {
            "email": "target@example.com",
            "password": "wrong-password-1234",
        }
        for _ in range(3):
            res = await self.client.post("/api/v1/auth/login", json=payload)
            self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        # 4th attempt exceeds max_attempts (3)
        res_blocked = await self.client.post("/api/v1/auth/login", json=payload)
        self.assertEqual(res_blocked.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("Too many authentication attempts", res_blocked.json()["detail"])

    async def test_logout_revokes_session(self) -> None:
        """Verify logout revokes the active session and prevents subsequent access."""
        reg_res = await self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "logout_test@example.com",
                "password": "super-secure-password-2026",
            },
        )
        csrf_token = reg_res.json()["csrf_token"]

        # Logout with CSRF header
        logout_res = await self.client.post(
            "/api/v1/auth/logout",
            headers={"X-CSRF-Token": csrf_token},
        )
        self.assertEqual(logout_res.status_code, status.HTTP_204_NO_CONTENT)

        # Subsequent introspection must be rejected
        me_res = await self.client.get("/api/v1/auth/me")
        self.assertEqual(me_res.status_code, status.HTTP_401_UNAUTHORIZED)

    async def test_cookie_csrf_enforcement_on_logout(self) -> None:
        """Verify that state-changing cookie requests without CSRF token are rejected with 403."""
        await self.client.post(
            "/api/v1/auth/register",
            json={
                "email": "csrf_test@example.com",
                "password": "super-secure-password-2026",
            },
        )

        # Attempt logout without X-CSRF-Token header
        res_no_csrf = await self.client.post("/api/v1/auth/logout")
        self.assertEqual(res_no_csrf.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("CSRF", res_no_csrf.json()["detail"])

    async def test_logout_all_sessions(self) -> None:
        """Verify logout-all revokes all active concurrent sessions for the user."""
        reg_payload = {
            "email": "logout_all@example.com",
            "password": "super-secure-password-2026",
        }
        res1 = await self.client.post("/api/v1/auth/register", json=reg_payload)
        session_token_1 = res1.cookies.get("dera_session")

        # Establish second session
        res2 = await self.client.post("/api/v1/auth/login", json=reg_payload)
        session_token_2 = res2.cookies.get("dera_session")
        csrf_token_2 = res2.json()["csrf_token"]

        # Issue logout-all from second session
        logout_all_res = await self.client.post(
            "/api/v1/auth/logout-all",
            headers={"X-CSRF-Token": csrf_token_2},
        )
        self.assertEqual(logout_all_res.status_code, status.HTTP_204_NO_CONTENT)

        # Both session tokens should now be rejected
        self.client.cookies.clear()
        assert session_token_1 is not None
        check1 = await self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {session_token_1}"},
        )
        self.assertEqual(check1.status_code, status.HTTP_401_UNAUTHORIZED)

        assert session_token_2 is not None
        check2 = await self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {session_token_2}"},
        )
        self.assertEqual(check2.status_code, status.HTTP_401_UNAUTHORIZED)


if __name__ == "__main__":
    unittest.main()
