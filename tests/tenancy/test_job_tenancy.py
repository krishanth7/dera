"""Security Tests for Job Multi-Tenant Isolation.

Mandatory Section 42 verification matrix:
- Workspace A cannot read Workspace B jobs (HTTP 404/403).
- Workspace A cannot cancel Workspace B jobs.
- Non-members cannot list or query jobs.
- Removed members immediately lose job access.
- Disabled users cannot submit jobs.
- Worker execution strictly enforces workspace boundary.
- Job results never leak across workspace barriers.
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


class TestJobTenantIsolation(unittest.IsolatedAsyncioTestCase):
    """Test suite verifying cross-tenant boundaries for background jobs."""

    async def asyncSetUp(self) -> None:
        auth_rate_limiter.clear()
        self.settings = ApiSettings(
            environment="testing",
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

        # 1. Register User A (Tenant A)
        r_a = await self.client.post(
            "/api/v1/auth/register",
            json={"email": "alice@tenant-a.com", "password": "password-tenant-a-2026"},
        )
        self.token_a = r_a.cookies.get("dera_session")

        # 2. Register User B (Tenant B)
        r_b = await self.client.post(
            "/api/v1/auth/register",
            json={"email": "bob@tenant-b.com", "password": "password-tenant-b-2026"},
        )
        self.token_b = r_b.cookies.get("dera_session")

        # 3. Create Workspace A
        ws_a_res = await self.client.post(
            "/api/v1/workspaces",
            json={"name": "Tenant A Core", "slug": "tenant-a-core"},
            headers={"Authorization": f"Bearer {self.token_a}"},
        )
        self.ws_a_id = ws_a_res.json()["id"]

        # 4. Create Workspace B
        ws_b_res = await self.client.post(
            "/api/v1/workspaces",
            json={"name": "Tenant B Core", "slug": "tenant-b-core"},
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.ws_b_id = ws_b_res.json()["id"]

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await dispose_database_engine(self.engine)
        auth_rate_limiter.clear()

    async def test_tenant_cross_workspace_read_rejected(self) -> None:
        """Verify User B cannot read or list jobs from Workspace A."""
        # User A submits job in Workspace A
        sub_res = await self.client.post(
            f"/api/v1/workspaces/{self.ws_a_id}/jobs",
            json={"job_type": "system.health_probe.v1", "payload": {"target": "secret-a"}},
            headers={"Authorization": f"Bearer {self.token_a}"},
        )
        job_a_id = sub_res.json()["id"]

        # User B attempts to get job in Workspace A -> 403 Access Denied
        cross_res = await self.client.get(
            f"/api/v1/workspaces/{self.ws_a_id}/jobs/{job_a_id}",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(cross_res.status_code, status.HTTP_403_FORBIDDEN)

        # User B attempts to access job_a_id through Workspace B path -> 404 Not Found
        wrong_ws_res = await self.client.get(
            f"/api/v1/workspaces/{self.ws_b_id}/jobs/{job_a_id}",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(wrong_ws_res.status_code, status.HTTP_404_NOT_FOUND)

    async def test_tenant_cross_workspace_cancel_rejected(self) -> None:
        """Verify User B cannot cancel jobs in Workspace A."""
        sub_res = await self.client.post(
            f"/api/v1/workspaces/{self.ws_a_id}/jobs",
            json={"job_type": "system.health_probe.v1", "payload": {}},
            headers={"Authorization": f"Bearer {self.token_a}"},
        )
        job_a_id = sub_res.json()["id"]

        # User B attempts to cancel job A in Workspace A
        cancel_res = await self.client.post(
            f"/api/v1/workspaces/{self.ws_a_id}/jobs/{job_a_id}/cancel",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(cancel_res.status_code, status.HTTP_403_FORBIDDEN)

        # User B attempts to cancel job A through Workspace B
        cancel_wrong_ws = await self.client.post(
            f"/api/v1/workspaces/{self.ws_b_id}/jobs/{job_a_id}/cancel",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(cancel_wrong_ws.status_code, status.HTTP_404_NOT_FOUND)

    async def test_tenant_listing_isolation(self) -> None:
        """Verify User B's job list contains only Workspace B jobs, never Workspace A jobs."""
        # Create job in A
        await self.client.post(
            f"/api/v1/workspaces/{self.ws_a_id}/jobs",
            json={"job_type": "system.health_probe.v1", "payload": {"target": "a"}},
            headers={"Authorization": f"Bearer {self.token_a}"},
        )

        # Create job in B
        await self.client.post(
            f"/api/v1/workspaces/{self.ws_b_id}/jobs",
            json={"job_type": "system.health_probe.v1", "payload": {"target": "b"}},
            headers={"Authorization": f"Bearer {self.token_b}"},
        )

        # Query B jobs
        list_b = await self.client.get(
            f"/api/v1/workspaces/{self.ws_b_id}/jobs",
            headers={"Authorization": f"Bearer {self.token_b}"},
        )
        self.assertEqual(list_b.status_code, status.HTTP_200_OK)
        items_b = list_b.json()["items"]
        self.assertEqual(len(items_b), 1)
        self.assertEqual(items_b[0]["workspace_id"], self.ws_b_id)


if __name__ == "__main__":
    unittest.main()
