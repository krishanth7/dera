"""Real session and tenancy checks using the established platform SQLite fixture."""

from unittest.mock import patch

from tests.security.test_workspace_authorization_regression import (
    TestWorkspaceAuthorizationRegression,
)


class TestSqlAnalysisAPI(TestWorkspaceAuthorizationRegression):
    async def call_analysis(self, workspace=None, token=None, body=None, **kwargs):
        return await self.client.post(
            "/api/v1/sql-engineering/analyze",
            params={"workspace_id": str(workspace or self.ws_active.id)},
            headers={"Authorization": f"Bearer {token or self.valid_raw_token}"},
            json=body or {"sql": "SELECT id FROM accounts", "dialect": "postgresql"},
            **kwargs,
        )

    async def test_analysis_authorized_no_customer_connection(self):
        with patch(
            "dera_connectors.base.connector.BaseConnector.connect",
            side_effect=AssertionError("customer execution"),
        ):
            response = await self.call_analysis()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["safety"], "read_only_candidate")

    async def test_analysis_cross_tenant(self):
        response = await self.call_analysis(workspace=self.ws_tenant_b.id)
        self.assertEqual(response.status_code, 403)

    async def test_analysis_unauthenticated(self):
        response = await self.client.post(
            "/api/v1/sql-engineering/analyze",
            params={"workspace_id": str(self.ws_active.id)},
            json={"sql": "SELECT 1", "dialect": "sqlite"},
        )
        self.assertEqual(response.status_code, 401)

    async def test_analysis_bad_token(self):
        self.assertEqual((await self.call_analysis(token="forged")).status_code, 401)

    async def test_analysis_rejects_identity_fields(self):
        response = await self.call_analysis(
            body={"sql": "SELECT 1", "dialect": "sqlite", "role": "owner"}
        )
        self.assertEqual(response.status_code, 422)

    async def test_analysis_limits(self):
        response = await self.call_analysis(body={"sql": "x" * 16385, "dialect": "sqlite"})
        self.assertEqual(response.status_code, 422)
        response = await self.call_analysis(body={"sql": "x" * 70000, "dialect": "sqlite"})
        self.assertEqual(response.status_code, 413)

    async def test_analysis_unknown_dialect(self):
        self.assertEqual(
            (await self.call_analysis(body={"sql": "SELECT 1", "dialect": "oracle"})).status_code,
            422,
        )

    async def test_analysis_expired_and_revoked_sessions(self):
        for token in (self.expired_raw_token, self.revoked_raw_token):
            self.assertEqual((await self.call_analysis(token=token)).status_code, 401)

    async def test_analysis_chunked_body_limit(self):
        async def chunks():
            for _ in range(10):
                yield b" " * 10000

        response = await self.client.post(
            "/api/v1/sql-engineering/analyze",
            params={"workspace_id": str(self.ws_active.id)},
            headers={
                "Authorization": f"Bearer {self.valid_raw_token}",
                "Content-Type": "application/json",
            },
            content=chunks(),
        )
        self.assertEqual(response.status_code, 413)

    async def test_analysis_cookie_csrf_required(self):
        self.settings.auth_csrf_enabled = True
        response = await self.client.post(
            "/api/v1/sql-engineering/analyze",
            params={"workspace_id": str(self.ws_active.id)},
            cookies={self.settings.auth_cookie_name: self.valid_raw_token},
            json={"sql": "SELECT 1", "dialect": "sqlite"},
        )
        self.assertEqual(response.status_code, 403)
