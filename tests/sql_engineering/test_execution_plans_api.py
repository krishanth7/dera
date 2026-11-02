"""Real sessions and workspace enforcement for imported plans; no auth overrides."""

import json
from unittest.mock import patch

from tests.security import test_workspace_authorization_regression as auth_fixture


class TestExecutionPlansAPI(auth_fixture.TestWorkspaceAuthorizationRegression):
    async def submit(self, token=None, workspace=None, **extra):
        return await self.client.post(
            "/api/v1/sql-engineering/execution-plans/analyze",
            params={"workspace_id": str(workspace or self.ws_active.id)},
            headers={"Authorization": f"Bearer {token or self.valid_raw_token}"},
            json={
                "dialect": "postgresql",
                "format": "postgresql-json",
                "plan_json": json.dumps({"Plan": {"Node Type": "Seq Scan"}}),
                **extra,
            },
        )

    async def test_valid_and_no_execution(self):
        with patch(
            "dera_connectors.base.connector.BaseConnector.connect",
            side_effect=AssertionError("execution"),
        ):
            result = await self.submit(sql="DELETE FROM accounts")
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual(result.headers.get("cache-control"), "no-store")
        self.assertEqual(result.json()["sql_diagnostics"]["analysis"]["safety"], "unsafe")

    async def test_auth_tenant_and_sessions(self):
        for token in ("invalid", self.revoked_raw_token, self.expired_raw_token):
            self.assertEqual((await self.submit(token=token)).status_code, 401)
        self.assertEqual((await self.submit(workspace=self.ws_tenant_b.id)).status_code, 403)
        self.assertEqual((await self.submit(workspace=self.ws_suspended.id)).status_code, 403)
        self.assertEqual((await self.submit(token=self.user_b_token)).status_code, 403)
        result = await self.client.post(
            "/api/v1/sql-engineering/execution-plans/analyze",
            params={"workspace_id": str(self.ws_active.id)},
            json={"dialect": "sqlite", "format": "sqlite-eqp", "plan_json": "[]"},
        )
        self.assertEqual(result.status_code, 401)

    async def test_safe_errors_size_and_identity(self):
        marker = "private-plan-secret"
        result = await self.submit(plan_json=marker)
        self.assertEqual(result.status_code, 422)
        self.assertNotIn(marker, result.text)
        self.assertEqual((await self.submit(role="owner")).status_code, 422)
        self.assertEqual((await self.submit(connection_id="customer")).status_code, 422)
        self.assertEqual((await self.submit(format="analyze")).status_code, 422)
        self.assertEqual((await self.submit(plan_json="x" * 6_500_001)).status_code, 413)
        self.assertEqual((await self.submit(plan_json="[" * 65 + "]" * 65)).status_code, 422)

    async def test_cookie_csrf(self):
        self.settings.auth_csrf_enabled = True
        self.client.cookies.set(self.settings.auth_cookie_name, self.valid_raw_token)
        result = await self.client.post(
            "/api/v1/sql-engineering/execution-plans/analyze",
            params={"workspace_id": str(self.ws_active.id)},
            json={"dialect": "sqlite", "format": "sqlite-eqp", "plan_json": "[]"},
        )
        self.assertEqual(result.status_code, 403)

    async def test_sensitive_plan_not_logged(self):
        import logging

        records = []

        class Capture(logging.Handler):
            def emit(self, record):
                records.append(record.getMessage())

        handler = Capture()
        logger = logging.getLogger()
        logger.addHandler(handler)
        marker = "private-plan-literal-12345"
        try:
            response = await self.submit(
                plan_json=json.dumps({"Plan": {"Node Type": "Seq Scan", "Filter": marker}})
            )
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(marker, "\n".join(records))
        finally:
            logger.removeHandler(handler)

    async def test_outer_envelope_depth_before_framework_decoder(self):
        response = await self.client.post(
            "/api/v1/sql-engineering/execution-plans/analyze",
            params={"workspace_id": str(self.ws_active.id)},
            headers={
                "Authorization": f"Bearer {self.valid_raw_token}",
                "Content-Type": "application/json",
            },
            content='{"plan_json":' + "[" * 2000 + "0" + "]" * 2000 + "}",
        )
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("RecursionError", response.text)

    async def test_full_size_import_with_outer_unicode_escape_overhead(self):
        plan = json.dumps({"Plan": {"Node Type": "Result", "Padding": ["a" * 10000] * 100}})
        self.assertLess(len(plan.encode()), 1_048_576)
        escaped = "".join(f"\\u{ord(char):04x}" for char in plan)
        body = '{"dialect":"postgresql","format":"postgresql-json","plan_json":"' + escaped + '"}'
        self.assertGreater(len(body), 6_000_000)
        response = await self.client.post(
            "/api/v1/sql-engineering/execution-plans/analyze",
            params={"workspace_id": str(self.ws_active.id)},
            headers={
                "Authorization": f"Bearer {self.valid_raw_token}",
                "Content-Type": "application/json",
            },
            content=body,
        )
        self.assertEqual(response.status_code, 200, response.text[:300])
        self.assertEqual(response.json()["summary"]["node_count"], 1)

    async def test_envelope_validation_runs_off_event_loop(self):
        from threading import get_ident

        from dera_api.api.v1.endpoints.sql_engineering import PlanBoundedRoute

        loop_thread = get_ident()
        threads = []
        original = PlanBoundedRoute.validate_body

        def validate(route, body):
            threads.append(get_ident())
            return original(route, body)

        with patch.object(PlanBoundedRoute, "validate_body", new=validate):
            self.assertEqual((await self.submit()).status_code, 200)
            self.assertEqual((await self.submit(token="forged")).status_code, 401)
        self.assertEqual(len(threads), 2)
        self.assertTrue(all(thread != loop_thread for thread in threads))
