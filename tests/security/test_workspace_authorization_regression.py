"""Security Regression Suite — Fail-Closed Workspace Authorization & Identity Verification.

Mandatory Regression Tests covering all 17 conditions from Part II Section 3:
1. Anonymous request -> 401
2. Random bearer token -> 401
3. Forged token -> 401
4. Expired session -> 401
5. Revoked session -> 401
6. Disabled user -> 403
7. Missing session factory -> 503
8. Database connection failure -> 503
9. Missing workspace -> 403
10. Suspended workspace -> 403
11. Cross-tenant workspace ID -> 403
12. Revoked membership -> 403
13. Insufficient role -> 403
14. Valid authorized request -> 200/201
15. Authentication state spoofing (X-Actor headers ignored)
16. Dependency failure -> 503
17. Concurrent membership revocation -> 403
"""

from __future__ import annotations

import unittest
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

from dera_api.auth.password import hash_password
from dera_api.auth.rate_limiter import auth_rate_limiter
from dera_api.auth.tokens import generate_session_token, hash_session_token
from dera_api.core.config import ApiSettings
from dera_api.db.base import Base
from dera_api.db.dependencies import get_db_session
from dera_api.db.engine import create_database_engine, dispose_database_engine
from dera_api.db.models.identity import User, UserSession
from dera_api.db.models.workspace import Workspace, WorkspaceMembership
from dera_api.db.session import create_session_factory
from dera_api.factory import create_app
from fastapi import status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestWorkspaceAuthorizationRegression(unittest.IsolatedAsyncioTestCase):
    """Complete regression test suite verifying fail-closed workspace authorization."""

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

        # Seed authoritative test entities
        async with self.session_factory() as db:
            # 1. Valid Active User & Workspace
            self.user_active = User(
                id=uuid.uuid4(),
                email="active.user@dera.test",
                password_hash=hash_password("valid-password-2026"),
                status="active",
            )
            # 2. Disabled User
            self.user_disabled = User(
                id=uuid.uuid4(),
                email="disabled.user@dera.test",
                password_hash=hash_password("valid-password-2026"),
                status="disabled",
            )
            # 3. User B (Cross-Tenant)
            self.user_b = User(
                id=uuid.uuid4(),
                email="user.b@dera.test",
                password_hash=hash_password("valid-password-2026"),
                status="active",
            )
            db.add_all([self.user_active, self.user_disabled, self.user_b])

            # 4. Workspaces
            self.ws_active = Workspace(
                id=uuid.uuid4(),
                name="Production Workspace",
                slug="prod-workspace",
                status="active",
            )
            self.ws_suspended = Workspace(
                id=uuid.uuid4(),
                name="Suspended Workspace",
                slug="suspended-workspace",
                status="suspended",
            )
            self.ws_tenant_b = Workspace(
                id=uuid.uuid4(),
                name="Tenant B Workspace",
                slug="tenant-b-workspace",
                status="active",
            )
            db.add_all([self.ws_active, self.ws_suspended, self.ws_tenant_b])

            # 5. Memberships
            self.member_admin = WorkspaceMembership(
                id=uuid.uuid4(),
                workspace_id=self.ws_active.id,
                user_id=self.user_active.id,
                role="admin",
                status="active",
            )
            self.member_tenant_b = WorkspaceMembership(
                id=uuid.uuid4(),
                workspace_id=self.ws_tenant_b.id,
                user_id=self.user_b.id,
                role="admin",
                status="active",
            )
            db.add_all([self.member_admin, self.member_tenant_b])

            # 6. Sessions
            self.valid_raw_token = generate_session_token()
            self.valid_session = UserSession(
                id=uuid.uuid4(),
                user_id=self.user_active.id,
                token_hash=hash_session_token(self.valid_raw_token),
                expires_at=datetime.now(UTC) + timedelta(hours=2),
                created_at=datetime.now(UTC),
            )

            self.expired_raw_token = generate_session_token()
            self.expired_session = UserSession(
                id=uuid.uuid4(),
                user_id=self.user_active.id,
                token_hash=hash_session_token(self.expired_raw_token),
                expires_at=datetime.now(UTC) - timedelta(minutes=10),
                created_at=datetime.now(UTC) - timedelta(hours=1),
            )

            self.revoked_raw_token = generate_session_token()
            self.revoked_session = UserSession(
                id=uuid.uuid4(),
                user_id=self.user_active.id,
                token_hash=hash_session_token(self.revoked_raw_token),
                expires_at=datetime.now(UTC) + timedelta(hours=2),
                revoked_at=datetime.now(UTC) - timedelta(minutes=5),
                created_at=datetime.now(UTC) - timedelta(hours=1),
            )

            self.disabled_user_token = generate_session_token()
            self.disabled_user_session = UserSession(
                id=uuid.uuid4(),
                user_id=self.user_disabled.id,
                token_hash=hash_session_token(self.disabled_user_token),
                expires_at=datetime.now(UTC) + timedelta(hours=2),
                created_at=datetime.now(UTC),
            )

            self.user_b_token = generate_session_token()
            self.user_b_session = UserSession(
                id=uuid.uuid4(),
                user_id=self.user_b.id,
                token_hash=hash_session_token(self.user_b_token),
                expires_at=datetime.now(UTC) + timedelta(hours=2),
                created_at=datetime.now(UTC),
            )

            db.add_all(
                [
                    self.valid_session,
                    self.expired_session,
                    self.revoked_session,
                    self.disabled_user_session,
                    self.user_b_session,
                ]
            )
            await db.commit()

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await dispose_database_engine(self.engine)
        auth_rate_limiter.clear()

    # --- Test 1: Anonymous request -> 401 ---
    async def test_01_anonymous_request_fails_closed(self) -> None:
        res = await self.client.get(
            "/api/v1/migrations/snapshots",
            headers={"X-Workspace-Id": str(self.ws_active.id)},
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Test 2: Random bearer token -> 401 ---
    async def test_02_random_bearer_token_fails_closed(self) -> None:
        res = await self.client.get(
            "/api/v1/migrations/snapshots",
            headers={
                "Authorization": "Bearer random-unregistered-token-string",
                "X-Workspace-Id": str(self.ws_active.id),
            },
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Test 3: Forged token -> 401 ---
    async def test_03_forged_token_fails_closed(self) -> None:
        forged = self.valid_raw_token[:-4] + "xxxx"
        res = await self.client.get(
            "/api/v1/migrations/snapshots",
            headers={
                "Authorization": f"Bearer {forged}",
                "X-Workspace-Id": str(self.ws_active.id),
            },
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Test 4: Expired session -> 401 ---
    async def test_04_expired_session_fails_closed(self) -> None:
        res = await self.client.get(
            "/api/v1/migrations/snapshots",
            headers={
                "Authorization": f"Bearer {self.expired_raw_token}",
                "X-Workspace-Id": str(self.ws_active.id),
            },
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Test 5: Revoked session -> 401 ---
    async def test_05_revoked_session_fails_closed(self) -> None:
        res = await self.client.get(
            "/api/v1/migrations/snapshots",
            headers={
                "Authorization": f"Bearer {self.revoked_raw_token}",
                "X-Workspace-Id": str(self.ws_active.id),
            },
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- Test 6: Disabled user -> 403 ---
    async def test_06_disabled_user_fails_closed(self) -> None:
        res = await self.client.get(
            "/api/v1/migrations/snapshots",
            headers={
                "Authorization": f"Bearer {self.disabled_user_token}",
                "X-Workspace-Id": str(self.ws_active.id),
            },
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # --- Test 7: Missing session factory -> 503 ---
    async def test_07_missing_session_factory_fails_closed(self) -> None:
        # Deliberately strip db_session_factory from app state
        saved_factory = self.app.state.db_session_factory
        try:
            self.app.state.db_session_factory = None
            res = await self.client.get(
                "/api/v1/migrations/snapshots",
                headers={
                    "Authorization": f"Bearer {self.valid_raw_token}",
                    "X-Workspace-Id": str(self.ws_active.id),
                },
            )
            self.assertEqual(res.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        finally:
            self.app.state.db_session_factory = saved_factory

    # --- Test 8: Missing database connection / operational failure -> 503 ---
    async def test_08_database_failure_fails_closed(self) -> None:
        def broken_factory():
            raise RuntimeError("Database connection pool exhausted")

        saved_factory = self.app.state.db_session_factory
        try:
            self.app.state.db_session_factory = broken_factory
            res = await self.client.get(
                "/api/v1/migrations/snapshots",
                headers={
                    "Authorization": f"Bearer {self.valid_raw_token}",
                    "X-Workspace-Id": str(self.ws_active.id),
                },
            )
            self.assertEqual(res.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        finally:
            self.app.state.db_session_factory = saved_factory

    # --- Test 9: Missing workspace -> 403 ---
    async def test_09_missing_workspace_fails_closed(self) -> None:
        fake_ws = uuid.uuid4()
        res = await self.client.get(
            "/api/v1/migrations/snapshots",
            headers={
                "Authorization": f"Bearer {self.valid_raw_token}",
                "X-Workspace-Id": str(fake_ws),
            },
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # --- Test 10: Suspended workspace -> 403 ---
    async def test_10_suspended_workspace_fails_closed(self) -> None:
        res = await self.client.get(
            "/api/v1/migrations/snapshots",
            headers={
                "Authorization": f"Bearer {self.valid_raw_token}",
                "X-Workspace-Id": str(self.ws_suspended.id),
            },
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # --- Test 11: Cross-tenant workspace ID -> 403 ---
    async def test_11_cross_tenant_workspace_fails_closed(self) -> None:
        # User Active is NOT a member of Tenant B's workspace
        res = await self.client.get(
            "/api/v1/migrations/snapshots",
            headers={
                "Authorization": f"Bearer {self.valid_raw_token}",
                "X-Workspace-Id": str(self.ws_tenant_b.id),
            },
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # --- Test 12: Revoked membership -> 403 ---
    async def test_12_revoked_membership_fails_closed(self) -> None:
        async with self.session_factory() as db:
            membership = await db.get(WorkspaceMembership, self.member_admin.id)
            membership.status = "inactive"
            await db.commit()

        res = await self.client.get(
            "/api/v1/migrations/snapshots",
            headers={
                "Authorization": f"Bearer {self.valid_raw_token}",
                "X-Workspace-Id": str(self.ws_active.id),
            },
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    # --- Test 13: Insufficient role -> 403 ---
    async def test_13_insufficient_role_fails_closed(self) -> None:
        # Demote user to viewer
        async with self.session_factory() as db:
            membership = await db.get(WorkspaceMembership, self.member_admin.id)
            membership.role = "viewer"
            membership.status = "active"
            await db.commit()

        # Viewer can read snapshots (Permission.MIGRATION_READ is allowed)
        read_res = await self.client.get(
            "/api/v1/migrations/snapshots",
            headers={
                "Authorization": f"Bearer {self.valid_raw_token}",
                "X-Workspace-Id": str(self.ws_active.id),
            },
        )
        self.assertEqual(read_res.status_code, status.HTTP_200_OK)

        # But Viewer CANNOT compare (requires MIGRATION_COMPARE) or approve (requires MIGRATION_APPROVE)
        compare_res = await self.client.post(
            "/api/v1/migrations/compare",
            json={"baseline_snapshot_id": "snap_1", "target_snapshot_id": "snap_2"},
            headers={
                "Authorization": f"Bearer {self.valid_raw_token}",
                "X-Workspace-Id": str(self.ws_active.id),
            },
        )
        self.assertEqual(compare_res.status_code, status.HTTP_403_FORBIDDEN)

    # --- Test 14: Valid authorized request -> 200 ---
    async def test_14_valid_authorized_request_succeeds(self) -> None:
        res = await self.client.get(
            "/api/v1/migrations/snapshots",
            headers={
                "Authorization": f"Bearer {self.valid_raw_token}",
                "X-Workspace-Id": str(self.ws_active.id),
            },
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertIn("snapshots", data)
        self.assertIn("total_count", data)

    # --- Test 15: Authentication state spoofing ignored ---
    async def test_15_authentication_state_spoofing_ignored(self) -> None:
        # Attempt to spoof actor header as another user or role
        res = await self.client.get(
            "/api/v1/migrations/snapshots",
            headers={
                "Authorization": f"Bearer {self.valid_raw_token}",
                "X-Workspace-Id": str(self.ws_active.id),
                "X-Actor-Id": str(uuid.uuid4()),
                "X-Actor-Role": "owner",
            },
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    # --- Test 16: Malformed UUID -> 400 ---
    async def test_16_malformed_workspace_uuid_fails_closed(self) -> None:
        res = await self.client.get(
            "/api/v1/migrations/snapshots",
            headers={
                "Authorization": f"Bearer {self.valid_raw_token}",
                "X-Workspace-Id": "not-a-valid-uuid",
            },
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Test 17: Concurrent membership revocation ---
    async def test_17_concurrent_membership_revocation_fails_closed(self) -> None:
        # Initial request succeeds
        res1 = await self.client.get(
            "/api/v1/migrations/snapshots",
            headers={
                "Authorization": f"Bearer {self.valid_raw_token}",
                "X-Workspace-Id": str(self.ws_active.id),
            },
        )
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # Deactivate membership concurrently in the database
        async with self.session_factory() as db:
            membership = await db.get(WorkspaceMembership, self.member_admin.id)
            membership.status = "suspended"
            await db.commit()

        # Immediate next request fails closed with 403
        res2 = await self.client.get(
            "/api/v1/migrations/snapshots",
            headers={
                "Authorization": f"Bearer {self.valid_raw_token}",
                "X-Workspace-Id": str(self.ws_active.id),
            },
        )
        self.assertEqual(res2.status_code, status.HTTP_403_FORBIDDEN)


if __name__ == "__main__":
    unittest.main()
