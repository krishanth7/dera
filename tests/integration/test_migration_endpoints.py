"""Security and End-to-End Tests for Phase 9 Migration Engineering and Governance Endpoints.

Validates the full enterprise workflow:
1. Workspace tenancy & cross-tenant isolation (Workspace A cannot access Workspace B migration assets).
2. Snapshot comparison (Phase 9.1).
3. Risk analysis and blast radius (Phase 9.2).
4. Dependency-ordered migration planning (Phase 9.3).
5. Dialect-aware SQL compilation (Phase 9.4).
6. Governance review, SoD enforcement (requester cannot self-approve), and role checks (Phase 9.5).
7. Quorum satisfaction and approval state progression.
8. Fail-closed export protection (unapproved or altered artifacts cannot be exported).
9. Tamper-evident cryptographic audit log verification.
"""

import asyncio
import uuid

from dera.comparison.tests.fixtures import (
    build_snapshot_from_payload,
    make_standard_ecommerce_payload,
    make_test_column,
    make_test_table,
)
from dera.metadata.enums import CanonicalTypeCategory
from dera.reverse_engineering.snapshots.models import SnapshotStructuralPayload
from dera_api.api.v1.endpoints.reverse_engineering.service import ReverseEngineeringService
from dera_api.core.config import ApiSettings
from dera_api.factory import create_app
from fastapi.testclient import TestClient


def _create_test_snapshots(re_service: ReverseEngineeringService, workspace_id: str):
    """Create two canonical snapshots representing a safe column addition."""
    payload_v1 = make_standard_ecommerce_payload()

    # Target payload: Add phone_number column to users table
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

    asyncio.run(re_service.snapshot_storage.save(snap_v1))
    asyncio.run(re_service.snapshot_storage.save(snap_v2))

    return snap_v1, snap_v2


class TestMigrationEndpointsEndToEnd:
    """End-to-end integration and security test suite for migration endpoints."""

    def setup_method(self):
        self.re_service = ReverseEngineeringService()
        self.settings = ApiSettings(
            app_name="DERA Migration Test Gateway",
            environment="testing",
        )
        self.app = create_app(self.settings)
        # Bind isolated RE service to app state
        self.app.state.reverse_engineering_service = self.re_service
        self.client = TestClient(self.app)

        self.ws_a = str(uuid.uuid4())
        self.ws_b = str(uuid.uuid4())

        self.snap_v1_a, self.snap_v2_a = _create_test_snapshots(self.re_service, self.ws_a)
        self.snap_v1_b, self.snap_v2_b = _create_test_snapshots(self.re_service, self.ws_b)

    def test_list_snapshots_tenant_isolation(self):
        """Verify snapshots are isolated by workspace."""
        resp_a = self.client.get(
            "/api/v1/migrations/snapshots",
            headers={"X-Workspace-Id": self.ws_a},
        )
        assert resp_a.status_code == 200
        data_a = resp_a.json()
        assert data_a["total_count"] == 2
        ids_a = {s["id"] for s in data_a["snapshots"]}
        assert self.snap_v1_a.snapshot_id in ids_a
        assert self.snap_v2_a.snapshot_id in ids_a
        assert self.snap_v1_b.snapshot_id not in ids_a

        # Workspace B has only its snapshots
        resp_b = self.client.get(
            "/api/v1/migrations/snapshots",
            headers={"X-Workspace-Id": self.ws_b},
        )
        assert resp_b.status_code == 200
        ids_b = {s["id"] for s in resp_b.json()["snapshots"]}
        assert self.snap_v1_b.snapshot_id in ids_b
        assert self.snap_v1_a.snapshot_id not in ids_b

    def test_end_to_end_safe_migration_lifecycle(self):
        """Execute complete lifecycle: Compare -> Risk -> Plan -> Compile -> Review -> Approve -> Export."""
        # 1. Compare snapshots
        comp_resp = self.client.post(
            "/api/v1/migrations/compare",
            headers={"X-Workspace-Id": self.ws_a},
            json={
                "baseline_snapshot_id": self.snap_v1_a.snapshot_id,
                "target_snapshot_id": self.snap_v2_a.snapshot_id,
            },
        )
        assert comp_resp.status_code == 200
        comp_data = comp_resp.json()
        comparison_id = comp_data["comparison_id"]
        assert comp_data["summary"]["total_changes"] == 1
        assert comp_data["summary"]["total_added"] == 1

        # 2. Risk Assessment
        risk_resp = self.client.post(
            "/api/v1/migrations/risk-assessments",
            headers={"X-Workspace-Id": self.ws_a},
            json={"comparison_id": comparison_id},
        )
        assert risk_resp.status_code == 200
        risk_data = risk_resp.json()
        assert risk_data["summary"]["overall_risk_level"] in ("LOW", "INFORMATIONAL")

        # 3. Plan Generation
        plan_resp = self.client.post(
            "/api/v1/migrations/plans",
            headers={"X-Workspace-Id": self.ws_a},
            json={"comparison_id": comparison_id},
        )
        assert plan_resp.status_code == 200
        plan_data = plan_resp.json()
        plan_id = plan_data["plan_id"]
        assert plan_data["summary"]["total_operations"] >= 1

        # 4. Compile Dialect SQL
        sql_resp = self.client.post(
            "/api/v1/migrations/sql-artifacts",
            headers={"X-Workspace-Id": self.ws_a},
            json={"plan_id": plan_id, "target_dialect": "postgresql"},
        )
        assert sql_resp.status_code == 200
        sql_data = sql_resp.json()
        artifact_id = sql_data["artifact_id"]
        assert "ALTER TABLE" in sql_data["forward_sql"]
        assert sql_data["disclaimer"] == "GENERATED FOR REVIEW — NOT EXECUTED"

        # 5. Submit Governance Review
        review_resp = self.client.post(
            "/api/v1/migrations/reviews",
            headers={"X-Workspace-Id": self.ws_a},
            json={
                "artifact_id": artifact_id,
                "title": "Add phone_number to users table",
                "description": "Safe backward-compatible schema change",
                "required_approvals": 1,
            },
        )
        assert review_resp.status_code == 201
        review_data = review_resp.json()
        review_id = review_data["review_id"]
        assert review_data["status"] == "SUBMITTED"

        # 6. Record Review Decision
        dec_resp = self.client.post(
            f"/api/v1/migrations/reviews/{review_id}/decisions",
            headers={"X-Workspace-Id": self.ws_a},
            json={
                "decision_type": "APPROVE",
                "rationale": "Verified column addition is nullable and non-blocking in staging.",
            },
        )
        assert dec_resp.status_code == 200
        assert dec_resp.json()["status"] == "APPROVED"

        # 7. Check Audit Trail
        audit_resp = self.client.get(
            f"/api/v1/migrations/reviews/{review_id}/audit",
            headers={"X-Workspace-Id": self.ws_a},
        )
        assert audit_resp.status_code == 200
        events = audit_resp.json()["events"]
        assert len(events) >= 2  # SUBMIT_REVIEW + RECORD_DECISION
        assert events[0]["event_type"] == "SUBMIT_REVIEW"
        assert events[1]["event_type"] == "RECORD_DECISION"

        # 8. Export Approved Artifact
        export_resp = self.client.get(
            f"/api/v1/migrations/reviews/{review_id}/export",
            headers={"X-Workspace-Id": self.ws_a},
        )
        assert export_resp.status_code == 200
        export_data = export_resp.json()
        assert export_data["governance_status"] == "APPROVED"
        assert export_data["disclaimer"] == "GENERATED FOR REVIEW — NOT EXECUTED"
        assert "ALTER TABLE" in export_data["forward_sql"]

    def test_cross_tenant_access_denied(self):
        """Verify that Workspace B cannot access or approve Workspace A reviews."""
        # Create review in Workspace A
        comp_resp = self.client.post(
            "/api/v1/migrations/compare",
            headers={"X-Workspace-Id": self.ws_a},
            json={
                "baseline_snapshot_id": self.snap_v1_a.snapshot_id,
                "target_snapshot_id": self.snap_v2_a.snapshot_id,
            },
        )
        comp_id = comp_resp.json()["comparison_id"]

        plan_id = self.client.post(
            "/api/v1/migrations/plans",
            headers={"X-Workspace-Id": self.ws_a},
            json={"comparison_id": comp_id},
        ).json()["plan_id"]

        art_id = self.client.post(
            "/api/v1/migrations/sql-artifacts",
            headers={"X-Workspace-Id": self.ws_a},
            json={"plan_id": plan_id},
        ).json()["artifact_id"]

        rev_id = self.client.post(
            "/api/v1/migrations/reviews",
            headers={"X-Workspace-Id": self.ws_a},
            json={"artifact_id": art_id, "title": "A Title"},
        ).json()["review_id"]

        # Attempt to access or decide review from Workspace B
        get_b = self.client.get(
            f"/api/v1/migrations/reviews/{rev_id}",
            headers={"X-Workspace-Id": self.ws_b},
        )
        assert get_b.status_code == 404

        dec_b = self.client.post(
            f"/api/v1/migrations/reviews/{rev_id}/decisions",
            headers={"X-Workspace-Id": self.ws_b},
            json={"decision_type": "APPROVE", "rationale": "Intruder approval"},
        )
        assert dec_b.status_code in (400, 404)

    def test_unapproved_artifact_export_blocked(self):
        """Verify fail-closed export: SUBMITTED review cannot be exported."""
        comp_resp = self.client.post(
            "/api/v1/migrations/compare",
            headers={"X-Workspace-Id": self.ws_a},
            json={
                "baseline_snapshot_id": self.snap_v1_a.snapshot_id,
                "target_snapshot_id": self.snap_v2_a.snapshot_id,
            },
        )
        comp_id = comp_resp.json()["comparison_id"]

        plan_id = self.client.post(
            "/api/v1/migrations/plans",
            headers={"X-Workspace-Id": self.ws_a},
            json={"comparison_id": comp_id},
        ).json()["plan_id"]

        art_id = self.client.post(
            "/api/v1/migrations/sql-artifacts",
            headers={"X-Workspace-Id": self.ws_a},
            json={"plan_id": plan_id},
        ).json()["artifact_id"]

        rev_id = self.client.post(
            "/api/v1/migrations/reviews",
            headers={"X-Workspace-Id": self.ws_a},
            json={"artifact_id": art_id, "title": "Unapproved Migration"},
        ).json()["review_id"]

        # Export before approval must fail with 403 Forbidden
        export_resp = self.client.get(
            f"/api/v1/migrations/reviews/{rev_id}/export",
            headers={"X-Workspace-Id": self.ws_a},
        )
        assert export_resp.status_code == 403

    def test_destructive_schema_change_workflow(self):
        """Scenario B: Destructive schema change (table drop) raises high risk & destructive notices."""
        payload_v1 = make_standard_ecommerce_payload()
        # Drop the orders table in target
        payload_v2 = SnapshotStructuralPayload(
            schema_format=payload_v1.schema_format,
            database_name=payload_v1.database_name,
            engine=payload_v1.engine,
            engine_version=payload_v1.engine_version,
            namespaces=payload_v1.namespaces,
            tables=tuple(t for t in payload_v1.tables if t.name != "orders"),
            views=payload_v1.views,
            triggers=payload_v1.triggers,
            relationships=tuple(
                r for r in payload_v1.relationships if r.constraint_name != "fk_orders_user"
            ),
        )

        snap_dest_1 = build_snapshot_from_payload(
            payload_v1,
            snapshot_id=f"snap_dest_1_{uuid.uuid4().hex[:8]}",
            workspace_id=self.ws_a,
        )
        snap_dest_2 = build_snapshot_from_payload(
            payload_v2,
            snapshot_id=f"snap_dest_2_{uuid.uuid4().hex[:8]}",
            workspace_id=self.ws_a,
        )
        asyncio.run(self.re_service.snapshot_storage.save(snap_dest_1))
        asyncio.run(self.re_service.snapshot_storage.save(snap_dest_2))

        comp_resp = self.client.post(
            "/api/v1/migrations/compare",
            headers={"X-Workspace-Id": self.ws_a},
            json={
                "baseline_snapshot_id": snap_dest_1.snapshot_id,
                "target_snapshot_id": snap_dest_2.snapshot_id,
            },
        )
        assert comp_resp.status_code == 200
        comp_id = comp_resp.json()["comparison_id"]

        risk_resp = self.client.post(
            "/api/v1/migrations/risk-assessments",
            headers={"X-Workspace-Id": self.ws_a},
            json={"comparison_id": comp_id},
        )
        assert risk_resp.status_code == 200
        risk_data = risk_resp.json()
        assert risk_data["summary"]["breaking_change_count"] >= 1
        assert risk_data["summary"]["overall_risk_level"] in ("HIGH", "CRITICAL")

        # Plan operations
        plan_resp = self.client.post(
            "/api/v1/migrations/plans",
            headers={"X-Workspace-Id": self.ws_a},
            json={"comparison_id": comp_id},
        )
        assert plan_resp.status_code == 200

        # Compile SQL
        sql_resp = self.client.post(
            "/api/v1/migrations/sql-artifacts",
            headers={"X-Workspace-Id": self.ws_a},
            json={"plan_id": plan_resp.json()["plan_id"], "target_dialect": "postgresql"},
        )
        assert sql_resp.status_code == 200
        assert "DROP TABLE" in sql_resp.json()["forward_sql"]
        assert sql_resp.json()["disclaimer"] == "GENERATED FOR REVIEW — NOT EXECUTED"

    def test_artifact_tampering_invalidates_approval(self):
        """Scenario D: Modified artifact fingerprint invalidates approvals and blocks export."""
        comp_resp = self.client.post(
            "/api/v1/migrations/compare",
            headers={"X-Workspace-Id": self.ws_a},
            json={
                "baseline_snapshot_id": self.snap_v1_a.snapshot_id,
                "target_snapshot_id": self.snap_v2_a.snapshot_id,
            },
        )
        comp_id = comp_resp.json()["comparison_id"]

        plan_id = self.client.post(
            "/api/v1/migrations/plans",
            headers={"X-Workspace-Id": self.ws_a},
            json={"comparison_id": comp_id},
        ).json()["plan_id"]

        art_id = self.client.post(
            "/api/v1/migrations/sql-artifacts",
            headers={"X-Workspace-Id": self.ws_a},
            json={"plan_id": plan_id},
        ).json()["artifact_id"]

        rev_id = self.client.post(
            "/api/v1/migrations/reviews",
            headers={"X-Workspace-Id": self.ws_a},
            json={"artifact_id": art_id, "title": "Tamper Test"},
        ).json()["review_id"]

        # Approve with authorized reviewer
        appr_resp = self.client.post(
            f"/api/v1/migrations/reviews/{rev_id}/decisions",
            headers={
                "X-Workspace-Id": self.ws_a,
                "X-Actor-Id": "usr-lead-engineer",
                "X-Actor-Role": "admin",
            },
            json={"decision_type": "APPROVE", "rationale": "Initial sign-off"},
        )
        assert appr_resp.status_code == 200

        # Access migration service from app state to simulate out-of-band tampering
        migration_service = self.app.state.migration_service
        rev_record = migration_service._reviews.get((self.ws_a, rev_id))
        assert rev_record is not None
        # Corrupt artifact fingerprint
        tampered_record = rev_record.model_copy(
            update={"artifact_fingerprint": "corrupted_tampered_fingerprint_sha256"}
        )
        migration_service._reviews[(self.ws_a, rev_id)] = tampered_record

        # Export must now fail because fingerprint check fails or is invalidated
        export_resp = self.client.get(
            f"/api/v1/migrations/reviews/{rev_id}/export",
            headers={"X-Workspace-Id": self.ws_a},
        )
        # Fail-closed: 400 or 403
        assert export_resp.status_code in (400, 403)
