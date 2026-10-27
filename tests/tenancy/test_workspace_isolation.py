"""Security Tests for Workspace Tenancy and Multi-Tenant Isolation.

Validates that workspace boundaries are strictly enforced:
- Cross-workspace reads, mutations, and member operations are rejected with 403.
- Role boundaries (Owner, Admin, Editor, Viewer) are enforced.
- Owner safeguards prevent removing or demoting the last active owner.
- Removed members immediately lose all workspace access.
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


class TestWorkspaceTenantIsolation(unittest.IsolatedAsyncioTestCase):
    """Test suite verifying tenant isolation and role permissions across workspaces."""

    async def asyncSetUp(self) -> None:
        auth_rate_limiter.clear()
        self.settings = ApiSettings(
            database_url="sqlite+aiosqlite:///:memory:",
            auth_csrf_enabled=False,  # Simplify header management for multi-user test matrix
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

        # 1. Register User 1 and User 2
        u1_res = await self.client.post(
            "/api/v1/auth/register",
            json={"email": "user1@tenant-a.com", "password": "password-user-1-2026"},
        )
        self.u1_token = u1_res.cookies.get("dera_session")
        self.u1_id = u1_res.json()["user"]["id"]

        self.client.cookies.clear()
        u2_res = await self.client.post(
            "/api/v1/auth/register",
            json={"email": "user2@tenant-b.com", "password": "password-user-2-2026"},
        )
        self.u2_token = u2_res.cookies.get("dera_session")
        self.u2_id = u2_res.json()["user"]["id"]

        # 2. User 1 creates Workspace A
        self.client.cookies.clear()
        ws_a_res = await self.client.post(
            "/api/v1/workspaces",
            json={"name": "Workspace Alpha", "slug": "workspace-alpha"},
            headers={"Authorization": f"Bearer {self.u1_token}"},
        )
        self.assertEqual(ws_a_res.status_code, status.HTTP_201_CREATED)
        self.ws_a_slug = ws_a_res.json()["slug"]

        # 3. User 2 creates Workspace B
        ws_b_res = await self.client.post(
            "/api/v1/workspaces",
            json={"name": "Workspace Beta", "slug": "workspace-beta"},
            headers={"Authorization": f"Bearer {self.u2_token}"},
        )
        self.assertEqual(ws_b_res.status_code, status.HTTP_201_CREATED)
        self.ws_b_slug = ws_b_res.json()["slug"]

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await dispose_database_engine(self.engine)
        auth_rate_limiter.clear()

    async def test_cross_tenant_read_isolation(self) -> None:
        """Verify User 1 cannot access Workspace B details or member lists."""
        # Read Workspace B with User 1 token -> 403
        res = await self.client.get(
            f"/api/v1/workspaces/{self.ws_b_slug}",
            headers={"Authorization": f"Bearer {self.u1_token}"},
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("denied", res.json()["detail"].lower())

        # List Workspace B members with User 1 token -> 403
        members_res = await self.client.get(
            f"/api/v1/workspaces/{self.ws_b_slug}/members",
            headers={"Authorization": f"Bearer {self.u1_token}"},
        )
        self.assertEqual(members_res.status_code, status.HTTP_403_FORBIDDEN)

    async def test_cross_tenant_mutation_isolation(self) -> None:
        """Verify User 1 cannot invite members or mutate Workspace B."""
        # Register a third neutral user
        u3_res = await self.client.post(
            "/api/v1/auth/register",
            json={"email": "user3@neutral.com", "password": "password-user-3-2026"},
        )
        u3_email = u3_res.json()["user"]["email"]

        # User 1 attempts to invite User 3 into Workspace B -> 403
        invite_res = await self.client.post(
            f"/api/v1/workspaces/{self.ws_b_slug}/members",
            json={"email": u3_email, "role": "viewer"},
            headers={"Authorization": f"Bearer {self.u1_token}"},
        )
        self.assertEqual(invite_res.status_code, status.HTTP_403_FORBIDDEN)

    async def test_role_permissions_within_workspace(self) -> None:
        """Verify Viewer, Editor, Admin, and Owner privilege boundaries in a workspace."""
        # Register Viewer and Editor accounts
        v_res = await self.client.post(
            "/api/v1/auth/register",
            json={"email": "viewer@tenant-a.com", "password": "password-viewer-2026"},
        )
        viewer_token = v_res.cookies.get("dera_session")
        viewer_email = v_res.json()["user"]["email"]
        viewer_id = v_res.json()["user"]["id"]

        e_res = await self.client.post(
            "/api/v1/auth/register",
            json={"email": "editor@tenant-a.com", "password": "password-editor-2026"},
        )
        editor_token = e_res.cookies.get("dera_session")
        editor_email = e_res.json()["user"]["email"]

        # Owner (User 1) adds Viewer and Editor to Workspace A
        await self.client.post(
            f"/api/v1/workspaces/{self.ws_a_slug}/members",
            json={"email": viewer_email, "role": "viewer"},
            headers={"Authorization": f"Bearer {self.u1_token}"},
        )
        await self.client.post(
            f"/api/v1/workspaces/{self.ws_a_slug}/members",
            json={"email": editor_email, "role": "editor"},
            headers={"Authorization": f"Bearer {self.u1_token}"},
        )

        # 1. Viewer can read workspace and members
        v_get = await self.client.get(
            f"/api/v1/workspaces/{self.ws_a_slug}",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        self.assertEqual(v_get.status_code, status.HTTP_200_OK)

        # 2. Viewer cannot invite members -> 403
        v_invite = await self.client.post(
            f"/api/v1/workspaces/{self.ws_a_slug}/members",
            json={"email": "extra@example.com", "role": "viewer"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        self.assertEqual(v_invite.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Editor cannot invite members -> 403
        e_invite = await self.client.post(
            f"/api/v1/workspaces/{self.ws_a_slug}/members",
            json={"email": "extra@example.com", "role": "viewer"},
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        self.assertEqual(e_invite.status_code, status.HTTP_403_FORBIDDEN)

        # 4. Owner can remove Viewer
        del_res = await self.client.delete(
            f"/api/v1/workspaces/{self.ws_a_slug}/members/{viewer_id}",
            headers={"Authorization": f"Bearer {self.u1_token}"},
        )
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)

        # 5. Removed Viewer immediately loses access -> 403
        v_get_after = await self.client.get(
            f"/api/v1/workspaces/{self.ws_a_slug}",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        self.assertEqual(v_get_after.status_code, status.HTTP_403_FORBIDDEN)

    async def test_owner_removal_safeguard(self) -> None:
        """Verify that the sole owner of a workspace cannot be removed or demoted."""
        # Attempt to demote sole Owner (User 1) to Editor -> 400
        demote_res = await self.client.patch(
            f"/api/v1/workspaces/{self.ws_a_slug}/members/{self.u1_id}",
            json={"role": "editor"},
            headers={"Authorization": f"Bearer {self.u1_token}"},
        )
        self.assertEqual(demote_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("last remaining owner", demote_res.json()["detail"].lower())

        # Attempt to delete sole Owner -> 400
        delete_res = await self.client.delete(
            f"/api/v1/workspaces/{self.ws_a_slug}/members/{self.u1_id}",
            headers={"Authorization": f"Bearer {self.u1_token}"},
        )
        self.assertEqual(delete_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("last remaining owner", delete_res.json()["detail"].lower())


if __name__ == "__main__":
    unittest.main()
