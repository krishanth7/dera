"""Diagnostics endpoint real-session, tenant isolation and snapshot integrity regressions."""

from unittest.mock import patch

from dera_api.api.v1.endpoints.reverse_engineering.service import ReverseEngineeringService

from tests.security import test_workspace_authorization_regression as auth_fixture
from tests.sql_engineering.diagnostics_fixtures import snapshot


class TestSqlDiagnosticsAPI(auth_fixture.TestWorkspaceAuthorizationRegression):
    async def asyncSetUp(self):
        await super().asyncSetUp()
        self.service = ReverseEngineeringService()
        self.app.state.reverse_engineering_service = self.service
        await self.service.snapshot_storage.save(snapshot(str(self.ws_active.id)))

    async def diagnose(self, token=None, workspace=None, **payload):
        body = {"sql": "SELECT * FROM accounts", "dialect": "postgresql", **payload}
        return await self.client.post(
            "/api/v1/sql-engineering/diagnostics",
            params={"workspace_id": str(workspace or self.ws_active.id)},
            headers={"Authorization": f"Bearer {token or self.valid_raw_token}"},
            json=body,
        )

    async def test_authorized_snapshot(self):
        response = await self.diagnose(schema_snapshot_id="snap_test")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNotNone(response.json()["snapshot_fingerprint"])

    async def test_missing_schema_and_options(self):
        response = await self.diagnose(
            options={"include_complexity": False, "include_recommendations": False}
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIsNone(result["complexity"])
        self.assertEqual(result["recommendations"], [])
        self.assertTrue(any(e["status"] == "NOT_EVALUATED" for e in result["rule_evaluations"]))

    async def test_cross_tenant_snapshot(self):
        foreign = snapshot(str(self.ws_tenant_b.id)).model_copy(
            update={"snapshot_id": "snap_foreign"}
        )
        await self.service.snapshot_storage.save(foreign)
        response = await self.diagnose(schema_snapshot_id="snap_foreign")
        self.assertEqual(response.status_code, 404)
        with patch.object(self.service, "get_snapshot", return_value=foreign):
            response = await self.diagnose(schema_snapshot_id="snap_foreign")
        self.assertEqual(response.status_code, 404)

    async def test_authentication_and_workspace_isolation(self):
        for token in ("forged", self.revoked_raw_token, self.expired_raw_token):
            self.assertEqual((await self.diagnose(token=token)).status_code, 401)
        self.assertEqual((await self.diagnose(workspace=self.ws_tenant_b.id)).status_code, 403)
        response = await self.client.post(
            "/api/v1/sql-engineering/diagnostics",
            params={"workspace_id": str(self.ws_active.id)},
            json={"sql": "SELECT 1", "dialect": "sqlite"},
        )
        self.assertEqual(response.status_code, 401)

    async def test_identity_spoofing_size_malformed_and_integrity(self):
        self.assertEqual((await self.diagnose(role="owner")).status_code, 422)
        self.assertEqual((await self.diagnose(sql="x" * 16385)).status_code, 422)
        self.assertEqual((await self.diagnose(sql="x" * 70000)).status_code, 413)
        response = await self.diagnose(sql="SELECT FROM")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["analysis_status"], "INDETERMINATE")
        invalid = snapshot(str(self.ws_active.id)).model_copy(update={"fingerprint": "0" * 64})
        with patch.object(self.service, "get_snapshot", return_value=invalid):
            self.assertEqual((await self.diagnose(schema_snapshot_id="snap_test")).status_code, 422)

    async def test_no_connector_execution(self):
        with patch(
            "dera_connectors.base.connector.BaseConnector.connect",
            side_effect=AssertionError("execution"),
        ):
            response = await self.diagnose(sql="DELETE FROM accounts")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["analysis"]["safety"], "unsafe")
