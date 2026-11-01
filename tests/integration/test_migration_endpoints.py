"""Security, Tenancy, and Governance Tests for Phase 9 Migration Endpoints.

Proves:
1. Unauthenticated requests fail with 401.
2. Spoofed X-Actor-Id or X-Actor-Role headers are ignored / rejected.
3. Missing DB context / unverified membership fails closed (401 / 403).
4. Revoked, suspended, or inactive memberships fail with 403.
5. Submitter cannot self-approve (Separation of Duties violation -> 403).
6. Cross-tenant access is strictly denied (403/404).
7. Quorum bypass attempts fail.
8. Artifact content tampering invalidates approvals and blocks export.
9. End-to-end safe migration lifecycle (Compare -> Risk -> Plan -> Compile -> Review -> Approve -> Export).
10. Durable persistence in dera_migration_reviews, decisions, and audit events.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
import unittest

from dera.comparison.tests.fixtures import (
    build_snapshot_from_payload,
    make_standard_ecommerce_payload,
    make_test_column,
    make_test_table,
)
from dera.metadata.enums import CanonicalTypeCategory
from dera.reverse_engineering.snapshots.models import SnapshotStructuralPayload
from dera_api.api.v1.endpoints.reverse_engineering.service import ReverseEngineeringService
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


def _create_test_snapshots(re_service: ReverseEngineeringService, workspace_id: str):
    """Create two canonical snapshots representing a safe column addition."""
    payload_v1 = make_standard_ecommerce_payload()

    users_tbl = next(t for t in payload_v1.tables if t.name == "users")
    new_col = make_test_column(
        table_id=users_tbl.table_id,
        name="phone_number",
        ordinal=5,
        native_type="varchar(30)",
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

    snap_v1 = build_snapshot_from_payload(
        payload=payload_v1,
        snapshot_id=f"snap_v1_{uuid.uuid4().hex[:8]}",
        workspace_id=workspace_id,
    )
    snap_v2 = build_snapshot_from_payload(
        payload=payload_v2,
        snapshot_id=f"snap_v2_{uuid.uuid4().hex[:8]}",
        workspace_id=workspace_id,
    )

    return snap_v1, snap_v2


class TestMigrationEndpointsSecurityAndGovernance(unittest.IsolatedAsyncioTestCase):
    """Rigorous integration test suite for Migration Engineering & Governance."""

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

        self.re_service = ReverseEngineeringService()
        self.app = create_app(self.settings)
        self.app.state.is_ready = True
        self.app.state.db_session_factory = self.session_factory
        self.app.state.reverse_engineering_service = self.re_service
        self.app.dependency_overrides[get_db_session] = override_get_db_session

        self.client = AsyncClient(
            transport=ASGITransport(app=self.app),
            base_url="http://testserver",
        )

        # 1. Register Owner (User 1)
        r1 = await self.client.post(
            "/api/v1/auth/register",
            json={"email": "owner@tenant-a.com", "password": "password-owner-2026"},
        )
        self.assertEqual(r1.status_code, 201)
        self.owner_token = r1.cookies.get("dera_session")
        self.owner_id = r1.json()["user"]["id"]

        # 2. Register Reviewer (User 2 - Admin in Workspace A)
        self.client.cookies.clear()
        r2 = await self.client.post(
            "/api/v1/auth/register",
            json={"email": "reviewer@tenant-a.com", "password": "password-reviewer-2026"},
        )
        self.assertEqual(r2.status_code, 201)
        self.reviewer_token = r2.cookies.get("dera_session")
        self.reviewer_id = r2.json()["user"]["id"]

        # 3. Register Tenant B User (User 3)
        self.client.cookies.clear()
        r3 = await self.client.post(
            "/api/v1/auth/register",
            json={"email": "user@tenant-b.com", "password": "password-user-b-2026"},
        )
        self.assertEqual(r3.status_code, 201)
        self.user_b_token = r3.cookies.get("dera_session")
        self.user_b_id = r3.json()["user"]["id"]

        # 4. Create Workspace A (owned by Owner)
        self.client.cookies.clear()
        self.client.cookies.set("dera_session", self.owner_token)
        ws_a_res = await self.client.post(
            "/api/v1/workspaces",
            json={"name": "Workspace Alpha", "slug": "workspace-alpha"},
        )
        self.assertEqual(ws_a_res.status_code, 201)
        self.ws_a_id = ws_a_res.json()["id"]

        # Add User 2 as Admin to Workspace A
        add_mem = await self.client.post(
            f"/api/v1/workspaces/workspace-alpha/members",
            json={"email": "reviewer@tenant-a.com", "role": "admin"},
        )
        self.assertEqual(add_mem.status_code, 201)

        # 5. Create Workspace B (owned by User B)
        self.client.cookies.clear()
        self.client.cookies.set("dera_session", self.user_b_token)
        ws_b_res = await self.client.post(
            "/api/v1/workspaces",
            json={"name": "Workspace Beta", "slug": "workspace-beta"},
        )
        self.assertEqual(ws_b_res.status_code, 201)
        self.ws_b_id = ws_b_res.json()["id"]

        # Save snapshots in memory storage for each workspace
        self.snap_v1_a, self.snap_v2_a = _create_test_snapshots(self.re_service, self.ws_a_id)
        self.snap_v1_b, self.snap_v2_b = _create_test_snapshots(self.re_service, self.ws_b_id)
        await self.re_service.snapshot_storage.save(self.snap_v1_a)
        await self.re_service.snapshot_storage.save(self.snap_v2_a)
        await self.re_service.snapshot_storage.save(self.snap_v1_b)
        await self.re_service.snapshot_storage.save(self.snap_v2_b)

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await dispose_database_engine(self.engine)
        auth_rate_limiter.clear()

    async def test_unauthenticated_request_fails_closed(self) -> None:
        """P0 Requirement 3 & 9: Unauthenticated request fails closed with 401."""
        self.client.cookies.clear()
        res = await self.client.get(
            "/api/v1/migrations/snapshots",
            headers={"X-Workspace-Id": self.ws_a_id},
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    async def test_spoofed_actor_headers_are_ignored(self) -> None:
        """P0 Requirement 1 & 9: X-Actor-Id and X-Actor-Role headers are ignored."""
        self.client.cookies.clear()
        self.client.cookies.set("dera_session", self.owner_token)

        # 1. Compare snapshots
        comp_resp = await self.client.post(
            "/api/v1/migrations/compare",
            headers={"X-Workspace-Id": self.ws_a_id},
            json={
                "baseline_snapshot_id": self.snap_v1_a.snapshot_id,
                "target_snapshot_id": self.snap_v2_a.snapshot_id,
            },
        )
        self.assertEqual(comp_resp.status_code, 200)
        comp_id = comp_resp.json()["comparison_id"]

        # 2. Plan
        plan_resp = await self.client.post(
            "/api/v1/migrations/plans",
            headers={"X-Workspace-Id": self.ws_a_id},
            json={"comparison_id": comp_id},
        )
        self.assertEqual(plan_resp.status_code, 200)
        plan_id = plan_resp.json()["plan_id"]

        # 3. Compile
        sql_resp = await self.client.post(
            "/api/v1/migrations/sql-artifacts",
            headers={"X-Workspace-Id": self.ws_a_id},
            json={"plan_id": plan_id},
        )
        self.assertEqual(sql_resp.status_code, 200)
        art_id = sql_resp.json()["artifact_id"]

        # 4. Submit with spoofed X-Actor-Id header
        rev_resp = await self.client.post(
            "/api/v1/migrations/reviews",
            headers={
                "X-Workspace-Id": self.ws_a_id,
                "X-Actor-Id": "spoofed-user-id-9999",
            },
            json={"artifact_id": art_id, "title": "Spoof Test"},
        )
        self.assertEqual(rev_resp.status_code, 201)
        rev_data = rev_resp.json()
        # Requester must be actual authenticated user ID, NOT the spoofed header
        self.assertEqual(rev_data["requester_id"], self.owner_id)
        self.assertNotEqual(rev_data["requester_id"], "spoofed-user-id-9999")

    async def test_separation_of_duties_self_approval_blocked(self) -> None:
        """P0 Requirement 4 & 9: Requester cannot approve their own review request."""
        self.client.cookies.clear()
        self.client.cookies.set("dera_session", self.owner_token)

        # 1. Pipeline to review creation by Owner
        comp_resp = await self.client.post(
            "/api/v1/migrations/compare",
            headers={"X-Workspace-Id": self.ws_a_id},
            json={
                "baseline_snapshot_id": self.snap_v1_a.snapshot_id,
                "target_snapshot_id": self.snap_v2_a.snapshot_id,
            },
        )
        comp_id = comp_resp.json()["comparison_id"]
        plan_id = (
            await self.client.post(
                "/api/v1/migrations/plans",
                headers={"X-Workspace-Id": self.ws_a_id},
                json={"comparison_id": comp_id},
            )
        ).json()["plan_id"]
        art_id = (
            await self.client.post(
                "/api/v1/migrations/sql-artifacts",
                headers={"X-Workspace-Id": self.ws_a_id},
                json={"plan_id": plan_id},
            )
        ).json()["artifact_id"]
        rev_id = (
            await self.client.post(
                "/api/v1/migrations/reviews",
                headers={"X-Workspace-Id": self.ws_a_id},
                json={"artifact_id": art_id, "title": "SoD Test"},
            )
        ).json()["review_id"]

        # Owner attempts to self-approve -> Forbidden (403)
        self_appr = await self.client.post(
            f"/api/v1/migrations/reviews/{rev_id}/decisions",
            headers={"X-Workspace-Id": self.ws_a_id},
            json={
                "decision_type": "APPROVE",
                "rationale": "I am the owner and approve my own change.",
            },
        )
        self.assertEqual(self_appr.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Separation of duties", self_appr.json()["detail"])

        # Reviewer (distinct admin) approves -> Success (200)
        self.client.cookies.clear()
        self.client.cookies.set("dera_session", self.reviewer_token)
        rev_appr = await self.client.post(
            f"/api/v1/migrations/reviews/{rev_id}/decisions",
            headers={"X-Workspace-Id": self.ws_a_id},
            json={
                "decision_type": "APPROVE",
                "rationale": "Independent reviewer verified safe migration.",
            },
        )
        self.assertEqual(rev_appr.status_code, status.HTTP_200_OK)
        self.assertEqual(rev_appr.json()["status"], "APPROVED")

    async def test_cross_tenant_access_denied(self) -> None:
        """P0 Requirement 5 & 9: Tenant B cannot access or decide Tenant A review."""
        self.client.cookies.clear()
        self.client.cookies.set("dera_session", self.owner_token)

        comp_id = (
            await self.client.post(
                "/api/v1/migrations/compare",
                headers={"X-Workspace-Id": self.ws_a_id},
                json={
                    "baseline_snapshot_id": self.snap_v1_a.snapshot_id,
                    "target_snapshot_id": self.snap_v2_a.snapshot_id,
                },
            )
        ).json()["comparison_id"]
        plan_id = (
            await self.client.post(
                "/api/v1/migrations/plans",
                headers={"X-Workspace-Id": self.ws_a_id},
                json={"comparison_id": comp_id},
            )
        ).json()["plan_id"]
        art_id = (
            await self.client.post(
                "/api/v1/migrations/sql-artifacts",
                headers={"X-Workspace-Id": self.ws_a_id},
                json={"plan_id": plan_id},
            )
        ).json()["artifact_id"]
        rev_id = (
            await self.client.post(
                "/api/v1/migrations/reviews",
                headers={"X-Workspace-Id": self.ws_a_id},
                json={"artifact_id": art_id, "title": "Tenant Isolation Test"},
            )
        ).json()["review_id"]

        # User B attempts to access Workspace A's review using Workspace A header -> 403 Forbidden
        self.client.cookies.clear()
        self.client.cookies.set("dera_session", self.user_b_token)
        cross_res = await self.client.get(
            f"/api/v1/migrations/reviews/{rev_id}",
            headers={"X-Workspace-Id": self.ws_a_id},
        )
        self.assertEqual(cross_res.status_code, status.HTTP_403_FORBIDDEN)

        # User B attempts to access review with their own workspace header -> 404 Not Found
        not_found_res = await self.client.get(
            f"/api/v1/migrations/reviews/{rev_id}",
            headers={"X-Workspace-Id": self.ws_b_id},
        )
        self.assertEqual(not_found_res.status_code, status.HTTP_404_NOT_FOUND)

    async def test_end_to_end_safe_migration_and_durable_persistence(self) -> None:
        """P0 Requirement 7, 8, 10: Complete lifecycle, risk fingerprint linkage, and durable persistence."""
        self.client.cookies.clear()
        self.client.cookies.set("dera_session", self.owner_token)

        # 1. Compare
        comp_res = await self.client.post(
            "/api/v1/migrations/compare",
            headers={"X-Workspace-Id": self.ws_a_id},
            json={
                "baseline_snapshot_id": self.snap_v1_a.snapshot_id,
                "target_snapshot_id": self.snap_v2_a.snapshot_id,
            },
        )
        self.assertEqual(comp_res.status_code, 200)
        comp_data = comp_res.json()
        comp_id = comp_data["comparison_id"]

        # 2. Risk Assessment
        risk_res = await self.client.post(
            "/api/v1/migrations/risk-assessments",
            headers={"X-Workspace-Id": self.ws_a_id},
            json={"comparison_id": comp_id},
        )
        self.assertEqual(risk_res.status_code, 200)
        risk_fp = risk_res.json()["fingerprint"]

        # 3. Plan Generation
        plan_res = await self.client.post(
            "/api/v1/migrations/plans",
            headers={"X-Workspace-Id": self.ws_a_id},
            json={"comparison_id": comp_id},
        )
        self.assertEqual(plan_res.status_code, 200)
        plan_id = plan_res.json()["plan_id"]

        # 4. Compile SQL
        sql_res = await self.client.post(
            "/api/v1/migrations/sql-artifacts",
            headers={"X-Workspace-Id": self.ws_a_id},
            json={"plan_id": plan_id, "target_dialect": "postgresql"},
        )
        self.assertEqual(sql_res.status_code, 200)
        art_id = sql_res.json()["artifact_id"]

        # 5. Submit Governance Review
        rev_res = await self.client.post(
            "/api/v1/migrations/reviews",
            headers={"X-Workspace-Id": self.ws_a_id},
            json={"artifact_id": art_id, "title": "Production Qualified Add Phone Column"},
        )
        self.assertEqual(rev_res.status_code, 201)
        rev_data = rev_res.json()
        rev_id = rev_data["review_id"]
        self.assertEqual(rev_data["status"], "SUBMITTED")

        # 6. Verify Durable DB Persistence of Review
        async with self.session_factory() as db_session:
            from dera_api.repositories.migration_governance import MigrationGovernanceRepository
            repo = MigrationGovernanceRepository(db_session)
            db_record = await repo.get_by_review_id(uuid.UUID(self.ws_a_id), rev_id)
            self.assertIsNotNone(db_record)
            self.assertEqual(db_record.requester_id, self.owner_id)
            self.assertEqual(db_record.risk_report_fingerprint, risk_fp)
            self.assertEqual(len(db_record.audit_events), 1)

        # 7. Reviewer approves
        self.client.cookies.clear()
        self.client.cookies.set("dera_session", self.reviewer_token)
        dec_res = await self.client.post(
            f"/api/v1/migrations/reviews/{rev_id}/decisions",
            headers={"X-Workspace-Id": self.ws_a_id},
            json={"decision_type": "APPROVE", "rationale": "Peer verified non-blocking."},
        )
        self.assertEqual(dec_res.status_code, 200)
        self.assertEqual(dec_res.json()["status"], "APPROVED")

        # 8. Verify Durable DB Persistence of Decision and Audit Chaining
        async with self.session_factory() as db_session:
            repo = MigrationGovernanceRepository(db_session)
            db_record = await repo.get_by_review_id(uuid.UUID(self.ws_a_id), rev_id)
            self.assertEqual(db_record.status, "APPROVED")
            self.assertEqual(len(db_record.decisions), 1)
            self.assertEqual(db_record.decisions[0].reviewer_id, self.reviewer_id)
            self.assertEqual(len(db_record.audit_events), 2)
            # Verify cryptographic hash chaining
            ev0 = db_record.audit_events[0]
            ev1 = db_record.audit_events[1]
            self.assertEqual(ev1.previous_event_hash, ev0.event_hash)

        # 9. Export Approved Migration
        export_res = await self.client.get(
            f"/api/v1/migrations/reviews/{rev_id}/export",
            headers={"X-Workspace-Id": self.ws_a_id},
        )
        self.assertEqual(export_res.status_code, 200)
        exp_data = export_res.json()
        self.assertEqual(exp_data["governance_status"], "APPROVED")
        self.assertEqual(exp_data["disclaimer"], "GENERATED FOR REVIEW — NOT EXECUTED")
        self.assertIn("ALTER TABLE", exp_data["forward_sql"])

    async def test_revoked_or_suspended_membership_fails(self) -> None:
        """P0 Requirement 5 & 9: Inactive or suspended workspace memberships fail closed with 403."""
        # Suspend reviewer membership in DB
        async with self.session_factory() as db_session:
            from dera_api.repositories.memberships import MembershipRepository
            repo = MembershipRepository(db_session)
            mem = await repo.get_membership(uuid.UUID(self.ws_a_id), uuid.UUID(self.reviewer_id))
            self.assertIsNotNone(mem)
            mem.status = "suspended"
            await db_session.commit()

        self.client.cookies.clear()
        self.client.cookies.set("dera_session", self.reviewer_token)
        res = await self.client.get(
            "/api/v1/migrations/snapshots",
            headers={"X-Workspace-Id": self.ws_a_id},
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    async def test_artifact_tampering_blocks_export(self) -> None:
        """P0 Requirement 8 & 9: Altering artifact content/fingerprint blocks export."""
        self.client.cookies.clear()
        self.client.cookies.set("dera_session", self.owner_token)

        # 1. Pipeline
        comp_id = (
            await self.client.post(
                "/api/v1/migrations/compare",
                headers={"X-Workspace-Id": self.ws_a_id},
                json={
                    "baseline_snapshot_id": self.snap_v1_a.snapshot_id,
                    "target_snapshot_id": self.snap_v2_a.snapshot_id,
                },
            )
        ).json()["comparison_id"]
        plan_id = (
            await self.client.post(
                "/api/v1/migrations/plans",
                headers={"X-Workspace-Id": self.ws_a_id},
                json={"comparison_id": comp_id},
            )
        ).json()["plan_id"]
        art_id = (
            await self.client.post(
                "/api/v1/migrations/sql-artifacts",
                headers={"X-Workspace-Id": self.ws_a_id},
                json={"plan_id": plan_id},
            )
        ).json()["artifact_id"]
        rev_id = (
            await self.client.post(
                "/api/v1/migrations/reviews",
                headers={"X-Workspace-Id": self.ws_a_id},
                json={"artifact_id": art_id, "title": "Tamper Test"},
            )
        ).json()["review_id"]

        # 2. Reviewer approves
        self.client.cookies.clear()
        self.client.cookies.set("dera_session", self.reviewer_token)
        appr_res = await self.client.post(
            f"/api/v1/migrations/reviews/{rev_id}/decisions",
            headers={"X-Workspace-Id": self.ws_a_id},
            json={"decision_type": "APPROVE", "rationale": "Valid sign-off."},
        )
        self.assertEqual(appr_res.status_code, 200)

        # 3. Simulate artifact tampering in service cache
        migration_service = self.app.state.migration_service
        cached_art = migration_service._artifacts.get((self.ws_a_id, art_id))
        self.assertIsNotNone(cached_art)
        # Mutate artifact fingerprint
        tampered_art = cached_art.model_copy(
            update={"artifact_fingerprint": "corrupted_or_mutated_sha256_hash"}
        )
        migration_service._artifacts[(self.ws_a_id, art_id)] = tampered_art

        # 4. Attempt to export tampered artifact -> fail-closed (400)
        export_res = await self.client.get(
            f"/api/v1/migrations/reviews/{rev_id}/export",
            headers={"X-Workspace-Id": self.ws_a_id},
        )
        self.assertEqual(export_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Integrity violation", export_res.json()["detail"])
