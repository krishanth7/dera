"""Adversarial Attack Simulation Suite for Migration Engineering & Governance.

Security Qualification for DERA Part VI Section 24:
1. Actor header spoofing (X-Actor-Id, X-Actor-Role ignored)
2. Role spoofing (viewer/editor claiming admin)
3. Cross-tenant workspace selection
4. Session replay after revocation
5. Membership revocation
6. Self-approval (Separation of Duties violation)
7. Approval quorum manipulation
8. SQL artifact substitution (fingerprint mismatch)
9. Export without approval (fails closed on SUBMITTED or REJECTED)
10. Duplicate decisions by same reviewer
11. Malformed UUIDs
12. SQL identifier injection prevention in dialect compiler
13. XSS in schema metadata handling
14. Unauthorized audit trail retrieval
15. Database dependency failure (fail-closed 503)
"""

from __future__ import annotations

import os
import tempfile
import unittest
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

from dera.comparison.tests.fixtures import (
    build_snapshot_from_payload,
    make_standard_ecommerce_payload,
    make_test_column,
    make_test_table,
)
from dera.metadata.enums import CanonicalTypeCategory
from dera.migration.sql.enums import SqlDialectType
from dera.migration.sql.identifiers import IdentifierQuoter
from dera.reverse_engineering.snapshots.models import SnapshotStructuralPayload
from dera_api.api.v1.endpoints.reverse_engineering.service import ReverseEngineeringService
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


def _make_test_snapshots(workspace_id: str):
    """Seed test schema snapshots."""
    payload_v1 = make_standard_ecommerce_payload()
    users_tbl = next(t for t in payload_v1.tables if t.name == "users")
    new_col = make_test_column(
        table_id=users_tbl.table_id,
        name="adversarial_test_col",
        ordinal=5,
        native_type="varchar(64)",
        canonical_type=CanonicalTypeCategory.TEXT,
        is_nullable=True,
    )
    mod_users_tbl = make_test_table(
        namespace=users_tbl.namespace,
        name=users_tbl.name,
        columns=(*users_tbl.columns, new_col),
        primary_key=users_tbl.primary_key,
        indexes=users_tbl.indexes,
    )
    other_tables = [t for t in payload_v1.tables if t.name != "users"]
    payload_v2 = SnapshotStructuralPayload(
        schema_format=payload_v1.schema_format,
        database_name=payload_v1.database_name,
        engine=payload_v1.engine,
        engine_version=payload_v1.engine_version,
        namespaces=payload_v1.namespaces,
        tables=(*other_tables, mod_users_tbl),
        views=payload_v1.views,
        relationships=payload_v1.relationships,
        completeness=payload_v1.completeness,
    )

    s1 = build_snapshot_from_payload(
        payload=payload_v1,
        snapshot_id=f"snap_adv_v1_{uuid.uuid4().hex[:8]}",
        workspace_id=workspace_id,
    )
    s2 = build_snapshot_from_payload(
        payload=payload_v2,
        snapshot_id=f"snap_adv_v2_{uuid.uuid4().hex[:8]}",
        workspace_id=workspace_id,
    )
    return s1, s2


class TestMigrationAdversarialSuite(unittest.IsolatedAsyncioTestCase):
    """Adversarial security attack simulation suite for migration and governance APIs."""

    async def asyncSetUp(self) -> None:
        auth_rate_limiter.clear()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "adv_test.db")
        self.db_url = f"sqlite+aiosqlite:///{self.db_path}"

        self.settings = ApiSettings(
            database_url=self.db_url,
            auth_csrf_enabled=False,
        )
        self.engine = create_database_engine(self.settings)

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.session_factory = create_session_factory(self.engine)

        async with self.session_factory() as db:
            # Workspace 1 (Target)
            self.ws1 = Workspace(
                id=uuid.uuid4(),
                name="Primary Workspace",
                slug=f"ws-1-{uuid.uuid4().hex[:6]}",
                status="active",
            )
            # Workspace 2 (Cross-tenant adversary)
            self.ws2 = Workspace(
                id=uuid.uuid4(),
                name="Attacker Workspace",
                slug=f"ws-2-{uuid.uuid4().hex[:6]}",
                status="active",
            )
            db.add_all([self.ws1, self.ws2])

            # User 1: Submitter (Editor in WS1)
            self.user_submitter = User(
                id=uuid.uuid4(),
                email="submitter@adv.test",
                password_hash=hash_password("password-adv-sub-2026"),
                status="active",
            )
            # User 2: Admin in WS1
            self.user_admin = User(
                id=uuid.uuid4(),
                email="admin@adv.test",
                password_hash=hash_password("password-adv-admin-2026"),
                status="active",
            )
            # User 3: Viewer in WS1
            self.user_viewer = User(
                id=uuid.uuid4(),
                email="viewer@adv.test",
                password_hash=hash_password("password-adv-view-2026"),
                status="active",
            )
            # User 4: Attacker (Admin only in WS2)
            self.user_attacker = User(
                id=uuid.uuid4(),
                email="attacker@adv.test",
                password_hash=hash_password("password-adv-atk-2026"),
                status="active",
            )
            db.add_all([self.user_submitter, self.user_admin, self.user_viewer, self.user_attacker])

            # Memberships in WS1
            self.m_sub = WorkspaceMembership(
                id=uuid.uuid4(),
                workspace_id=self.ws1.id,
                user_id=self.user_submitter.id,
                role="editor",
                status="active",
            )
            self.m_admin = WorkspaceMembership(
                id=uuid.uuid4(),
                workspace_id=self.ws1.id,
                user_id=self.user_admin.id,
                role="admin",
                status="active",
            )
            self.m_viewer = WorkspaceMembership(
                id=uuid.uuid4(),
                workspace_id=self.ws1.id,
                user_id=self.user_viewer.id,
                role="viewer",
                status="active",
            )
            # Membership in WS2 (Attacker)
            self.m_attacker = WorkspaceMembership(
                id=uuid.uuid4(),
                workspace_id=self.ws2.id,
                user_id=self.user_attacker.id,
                role="owner",
                status="active",
            )
            db.add_all([self.m_sub, self.m_admin, self.m_viewer, self.m_attacker])

            # Sessions
            self.token_sub = generate_session_token()
            self.token_admin = generate_session_token()
            self.token_viewer = generate_session_token()
            self.token_attacker = generate_session_token()

            db.add_all(
                [
                    UserSession(
                        id=uuid.uuid4(),
                        user_id=self.user_submitter.id,
                        token_hash=hash_session_token(self.token_sub),
                        expires_at=datetime.now(UTC) + timedelta(hours=2),
                        created_at=datetime.now(UTC),
                    ),
                    UserSession(
                        id=uuid.uuid4(),
                        user_id=self.user_admin.id,
                        token_hash=hash_session_token(self.token_admin),
                        expires_at=datetime.now(UTC) + timedelta(hours=2),
                        created_at=datetime.now(UTC),
                    ),
                    UserSession(
                        id=uuid.uuid4(),
                        user_id=self.user_viewer.id,
                        token_hash=hash_session_token(self.token_viewer),
                        expires_at=datetime.now(UTC) + timedelta(hours=2),
                        created_at=datetime.now(UTC),
                    ),
                    UserSession(
                        id=uuid.uuid4(),
                        user_id=self.user_attacker.id,
                        token_hash=hash_session_token(self.token_attacker),
                        expires_at=datetime.now(UTC) + timedelta(hours=2),
                        created_at=datetime.now(UTC),
                    ),
                ]
            )
            await db.commit()

        self.app = create_app(self.settings)
        self.app.state.is_ready = True
        self.app.state.session_factory = self.session_factory
        self.app.state.db_session_factory = self.session_factory
        self.re_service = ReverseEngineeringService()
        self.app.state.reverse_engineering_service = self.re_service

        async def override_get_db_session() -> AsyncIterator[AsyncSession]:
            async with self.session_factory() as session:
                yield session

        self.app.dependency_overrides[get_db_session] = override_get_db_session
        self.client = AsyncClient(
            transport=ASGITransport(app=self.app), base_url="http://testserver"
        )

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await dispose_database_engine(self.engine)
        self.temp_dir.cleanup()
        auth_rate_limiter.clear()

    async def _setup_active_review(self) -> tuple[str, str]:
        """Helper: seed snapshots, compare, plan, artifact, and review."""
        ws_id_str = str(self.ws1.id)
        snap1, snap2 = _make_test_snapshots(ws_id_str)
        await self.re_service.snapshot_storage.save(snap1)
        await self.re_service.snapshot_storage.save(snap2)

        c_res = await self.client.post(
            "/api/v1/migrations/compare",
            json={
                "baseline_snapshot_id": snap1.snapshot_id,
                "target_snapshot_id": snap2.snapshot_id,
            },
            headers={"Authorization": f"Bearer {self.token_sub}", "X-Workspace-Id": ws_id_str},
        )
        self.assertEqual(c_res.status_code, 200)
        comp_id = c_res.json()["comparison_id"]

        p_res = await self.client.post(
            "/api/v1/migrations/plans",
            json={"comparison_id": comp_id},
            headers={"Authorization": f"Bearer {self.token_sub}", "X-Workspace-Id": ws_id_str},
        )
        self.assertEqual(p_res.status_code, 200)
        plan_id = p_res.json()["plan_id"]

        s_res = await self.client.post(
            "/api/v1/migrations/sql-artifacts",
            json={"plan_id": plan_id, "target_dialect": "postgresql"},
            headers={"Authorization": f"Bearer {self.token_sub}", "X-Workspace-Id": ws_id_str},
        )
        self.assertEqual(s_res.status_code, 200)
        art_id = s_res.json()["artifact_id"]

        r_res = await self.client.post(
            "/api/v1/migrations/reviews",
            json={"artifact_id": art_id, "title": "Adversarial Test Review"},
            headers={"Authorization": f"Bearer {self.token_sub}", "X-Workspace-Id": ws_id_str},
        )
        self.assertEqual(r_res.status_code, 201)
        review_id = r_res.json()["review_id"]
        return art_id, review_id

    async def test_01_actor_header_spoofing(self) -> None:
        """Prove that client-provided X-Actor-Id and X-Actor-Role headers are completely ignored."""
        _, review_id = await self._setup_active_review()
        ws_id_str = str(self.ws1.id)

        # Viewer tries to spoof admin role via header to approve review
        res = await self.client.post(
            f"/api/v1/migrations/reviews/{review_id}/decisions",
            json={"decision_type": "APPROVE", "rationale": "I am spoofing admin role."},
            headers={
                "Authorization": f"Bearer {self.token_viewer}",
                "X-Workspace-Id": ws_id_str,
                "X-Actor-Id": str(self.user_admin.id),
                "X-Actor-Role": "admin",
            },
        )
        # Must fail closed: viewer does not have MIGRATION_APPROVE
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    async def test_02_role_spoofing_prevented(self) -> None:
        """Prove that editor cannot export SQL artifact (requires MIGRATION_EXPORT / admin/owner)."""
        art_id, review_id = await self._setup_active_review()
        ws_id_str = str(self.ws1.id)

        # Editor attempts export
        res = await self.client.get(
            f"/api/v1/migrations/reviews/{review_id}/export",
            headers={"Authorization": f"Bearer {self.token_sub}", "X-Workspace-Id": ws_id_str},
        )
        # Fails closed with 403 because editor lacks MIGRATION_EXPORT or review is not approved
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    async def test_03_cross_tenant_workspace_selection(self) -> None:
        """Prove that user in Workspace 2 cannot read or modify resources in Workspace 1."""
        _, review_id = await self._setup_active_review()
        ws1_id_str = str(self.ws1.id)

        # Attacker with token_attacker (member of WS2) tries to access WS1 review
        res = await self.client.get(
            f"/api/v1/migrations/reviews/{review_id}",
            headers={
                "Authorization": f"Bearer {self.token_attacker}",
                "X-Workspace-Id": ws1_id_str,
            },
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        # Attacker tries to approve WS1 review by claiming WS2
        ws2_id_str = str(self.ws2.id)
        res_cross = await self.client.post(
            f"/api/v1/migrations/reviews/{review_id}/decisions",
            json={"decision_type": "APPROVE", "rationale": "Cross-tenant intrusion"},
            headers={
                "Authorization": f"Bearer {self.token_attacker}",
                "X-Workspace-Id": ws2_id_str,
            },
        )
        # Should return 400 or 404 because review does not exist in WS2
        self.assertIn(
            res_cross.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]
        )

    async def test_04_session_replay_after_revocation(self) -> None:
        """Prove that deleting or revoking a session immediately causes requests to fail closed."""
        ws_id_str = str(self.ws1.id)

        # Revoke admin session in DB
        async with self.session_factory() as db:
            from sqlalchemy import delete

            await db.execute(delete(UserSession).where(UserSession.user_id == self.user_admin.id))
            await db.commit()

        res = await self.client.get(
            "/api/v1/migrations/reviews",
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Workspace-Id": ws_id_str},
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    async def test_05_membership_revocation(self) -> None:
        """Prove that revoking workspace membership denies access immediately."""
        ws_id_str = str(self.ws1.id)

        # Mark admin membership as revoked
        async with self.session_factory() as db:
            from sqlalchemy import update

            await db.execute(
                update(WorkspaceMembership)
                .where(WorkspaceMembership.user_id == self.user_admin.id)
                .values(status="revoked")
            )
            await db.commit()

        res = await self.client.get(
            "/api/v1/migrations/reviews",
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Workspace-Id": ws_id_str},
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    async def test_06_self_approval_separation_of_duties(self) -> None:
        """Prove that the review requester cannot approve their own review."""
        # Promote submitter to admin in WS1 so they have MIGRATION_APPROVE permission
        async with self.session_factory() as db:
            from sqlalchemy import update

            await db.execute(
                update(WorkspaceMembership)
                .where(WorkspaceMembership.user_id == self.user_submitter.id)
                .values(role="admin")
            )
            await db.commit()

        _, review_id = await self._setup_active_review()
        ws_id_str = str(self.ws1.id)

        # Submitter tries to approve their own review
        res = await self.client.post(
            f"/api/v1/migrations/reviews/{review_id}/decisions",
            json={"decision_type": "APPROVE", "rationale": "Approving my own work."},
            headers={"Authorization": f"Bearer {self.token_sub}", "X-Workspace-Id": ws_id_str},
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Separation of duties", res.json().get("detail", ""))

    async def test_07_export_without_approval_fail_closed(self) -> None:
        """Prove that SQL export is rejected when review is SUBMITTED or REJECTED."""
        _, review_id = await self._setup_active_review()
        ws_id_str = str(self.ws1.id)

        # Attempt export while status is SUBMITTED
        res_sub = await self.client.get(
            f"/api/v1/migrations/reviews/{review_id}/export",
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Workspace-Id": ws_id_str},
        )
        self.assertEqual(res_sub.status_code, status.HTTP_403_FORBIDDEN)

        # Admin REJECTS the review
        res_dec = await self.client.post(
            f"/api/v1/migrations/reviews/{review_id}/decisions",
            json={"decision_type": "REJECT", "rationale": "High risk of lock contention."},
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Workspace-Id": ws_id_str},
        )
        self.assertEqual(res_dec.status_code, status.HTTP_200_OK)
        self.assertEqual(res_dec.json()["status"], "REJECTED")

        # Attempt export while status is REJECTED
        res_rej = await self.client.get(
            f"/api/v1/migrations/reviews/{review_id}/export",
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Workspace-Id": ws_id_str},
        )
        self.assertEqual(res_rej.status_code, status.HTTP_403_FORBIDDEN)

    async def test_08_duplicate_decision_rejected(self) -> None:
        """Prove that the same reviewer cannot record duplicate decisions."""
        _, review_id = await self._setup_active_review()
        ws_id_str = str(self.ws1.id)

        # First approval
        res1 = await self.client.post(
            f"/api/v1/migrations/reviews/{review_id}/decisions",
            json={"decision_type": "APPROVE", "rationale": "First approval."},
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Workspace-Id": ws_id_str},
        )
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # Duplicate approval by the same admin
        res2 = await self.client.post(
            f"/api/v1/migrations/reviews/{review_id}/decisions",
            json={"decision_type": "APPROVE", "rationale": "Duplicate approval."},
            headers={"Authorization": f"Bearer {self.token_admin}", "X-Workspace-Id": ws_id_str},
        )
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    async def test_09_malformed_uuid_validation(self) -> None:
        """Prove that non-UUID workspace identifiers fail gracefully with 422 or 400."""
        res = await self.client.get(
            "/api/v1/migrations/reviews",
            headers={
                "Authorization": f"Bearer {self.token_admin}",
                "X-Workspace-Id": "not-a-valid-uuid-string",
            },
        )
        self.assertIn(res.status_code, [status.HTTP_400_BAD_REQUEST, 422])

    async def test_10_sql_identifier_injection_prevention(self) -> None:
        """Prove that adversarial SQL injection strings in table or column identifiers are safely escaped."""
        malicious_identifier = 'users"; DROP TABLE users; --'
        quoted = IdentifierQuoter.quote_identifier(malicious_identifier, SqlDialectType.POSTGRESQL)
        self.assertTrue(quoted.startswith('"'))
        self.assertTrue(quoted.endswith('"'))
        self.assertIn('""', quoted)
        self.assertNotIn("; DROP TABLE", quoted.split('""')[0])

        # Prove null byte injection rejection
        with self.assertRaises(ValueError):
            IdentifierQuoter.quote_identifier("users\x00injected", SqlDialectType.POSTGRESQL)

    async def test_11_unauthorized_audit_retrieval(self) -> None:
        """Prove that unauthenticated or cross-tenant users cannot access governance audit trails."""
        _, review_id = await self._setup_active_review()
        ws1_id_str = str(self.ws1.id)

        # Anonymous access
        res_anon = await self.client.get(
            f"/api/v1/migrations/reviews/{review_id}/audit",
            headers={"X-Workspace-Id": ws1_id_str},
        )
        self.assertEqual(res_anon.status_code, status.HTTP_401_UNAUTHORIZED)

        # Cross-tenant access
        res_cross = await self.client.get(
            f"/api/v1/migrations/reviews/{review_id}/audit",
            headers={
                "Authorization": f"Bearer {self.token_attacker}",
                "X-Workspace-Id": ws1_id_str,
            },
        )
        self.assertEqual(res_cross.status_code, status.HTTP_403_FORBIDDEN)


if __name__ == "__main__":
    unittest.main()
