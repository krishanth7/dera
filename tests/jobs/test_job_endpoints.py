"""Integration Tests for Background Job HTTP API Endpoints.

Validates HTTP REST routes:
- POST /api/v1/workspaces/{workspace_id}/jobs (submit)
- GET /api/v1/workspaces/{workspace_id}/jobs (list)
- GET /api/v1/workspaces/{workspace_id}/jobs/{job_id} (detail)
- POST /api/v1/workspaces/{workspace_id}/jobs/{job_id}/cancel (cancel)
- RBAC permissions: Viewer role prohibited from submit and cancel.
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


class TestJobEndpoints(unittest.IsolatedAsyncioTestCase):
    """Test suite validating HTTP REST endpoints for background jobs."""

    async def asyncSetUp(self) -> None:
        auth_rate_limiter.clear()
        self.settings = ApiSettings(
            environment="testing",
            database_url="sqlite+aiosqlite:///:memory:",
            auth_csrf_enabled=False,  # Bearer authentication mode
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

        # 1. Register Owner
        reg_res = await self.client.post(
            "/api/v1/auth/register",
            json={"email": "owner@company.com", "password": "secure-owner-pass-2026"},
        )
        self.assertEqual(reg_res.status_code, status.HTTP_201_CREATED)
        self.owner_token = reg_res.cookies.get("dera_session")

        # 2. Register Viewer
        viewer_reg = await self.client.post(
            "/api/v1/auth/register",
            json={"email": "viewer@company.com", "password": "secure-viewer-pass-2026"},
        )
        self.assertEqual(viewer_reg.status_code, status.HTTP_201_CREATED)
        self.viewer_token = viewer_reg.cookies.get("dera_session")

        # 3. Create Workspace as Owner
        ws_res = await self.client.post(
            "/api/v1/workspaces",
            json={"name": "Engineering Workspace", "slug": "eng-ws"},
            headers={"Authorization": f"Bearer {self.owner_token}"},
        )
        self.assertEqual(ws_res.status_code, status.HTTP_201_CREATED)
        self.workspace_id = ws_res.json()["id"]

        # 4. Add Viewer to Workspace
        add_res = await self.client.post(
            "/api/v1/workspaces/eng-ws/members",
            json={"email": "viewer@company.com", "role": "viewer"},
            headers={"Authorization": f"Bearer {self.owner_token}"},
        )
        self.assertEqual(add_res.status_code, status.HTTP_201_CREATED)

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await dispose_database_engine(self.engine)
        auth_rate_limiter.clear()

    async def test_submit_job_endpoint_success(self) -> None:
        """Verify Owner can submit a background job."""
        res = await self.client.post(
            f"/api/v1/workspaces/{self.workspace_id}/jobs",
            json={
                "job_type": "system.health_probe.v1",
                "payload": {"target": "http_test"},
                "priority": "normal",
            },
            headers={"Authorization": f"Bearer {self.owner_token}"},
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.json()
        self.assertEqual(data["job_type"], "system.health_probe.v1")
        self.assertEqual(data["workspace_id"], self.workspace_id)
        self.assertIn("id", data)

    async def test_submit_job_viewer_forbidden(self) -> None:
        """Verify Viewer role is prohibited from creating background jobs (HTTP 403)."""
        res = await self.client.post(
            f"/api/v1/workspaces/{self.workspace_id}/jobs",
            json={
                "job_type": "system.health_probe.v1",
                "payload": {},
            },
            headers={"Authorization": f"Bearer {self.viewer_token}"},
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(res.json()["code"], "PERMISSION_DENIED")

    async def test_list_and_get_job_endpoints(self) -> None:
        """Verify Viewer can list and view job details within the workspace."""
        # 1. Submit a job as Owner
        sub_res = await self.client.post(
            f"/api/v1/workspaces/{self.workspace_id}/jobs",
            json={"job_type": "system.health_probe.v1", "payload": {}},
            headers={"Authorization": f"Bearer {self.owner_token}"},
        )
        job_id = sub_res.json()["id"]

        # 2. List jobs as Viewer (requires job:read)
        list_res = await self.client.get(
            f"/api/v1/workspaces/{self.workspace_id}/jobs",
            headers={"Authorization": f"Bearer {self.viewer_token}"},
        )
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        list_data = list_res.json()
        self.assertGreaterEqual(list_data["total"], 1)
        self.assertEqual(list_data["items"][0]["id"], job_id)

        # 3. Retrieve specific job as Viewer
        get_res = await self.client.get(
            f"/api/v1/workspaces/{self.workspace_id}/jobs/{job_id}",
            headers={"Authorization": f"Bearer {self.viewer_token}"},
        )
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(get_res.json()["id"], job_id)

    async def test_cancel_job_endpoint(self) -> None:
        """Verify Owner can cancel job, while Viewer is forbidden."""
        sub_res = await self.client.post(
            f"/api/v1/workspaces/{self.workspace_id}/jobs",
            json={"job_type": "system.health_probe.v1", "payload": {}},
            headers={"Authorization": f"Bearer {self.owner_token}"},
        )
        job_id = sub_res.json()["id"]

        # Viewer attempts cancel -> 403 Forbidden
        viewer_cancel = await self.client.post(
            f"/api/v1/workspaces/{self.workspace_id}/jobs/{job_id}/cancel",
            headers={"Authorization": f"Bearer {self.viewer_token}"},
        )
        self.assertEqual(viewer_cancel.status_code, status.HTTP_403_FORBIDDEN)

        # Owner cancels -> 200 OK
        owner_cancel = await self.client.post(
            f"/api/v1/workspaces/{self.workspace_id}/jobs/{job_id}/cancel",
            headers={"Authorization": f"Bearer {self.owner_token}"},
        )
        self.assertEqual(owner_cancel.status_code, status.HTTP_200_OK)
        self.assertEqual(owner_cancel.json()["status"], "cancelled")


if __name__ == "__main__":
    unittest.main()
