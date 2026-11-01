"""DERA Repositories — Migration Artifacts Persistence Repository.

Provides data access routines for durable storage and retrieval of
Schema Comparisons, Migration Risks, Migration Plans, SQL Artifacts, and Exports.
Guarantees tenant workspace boundaries and cryptographic integrity.
"""

from __future__ import annotations

import uuid
from typing import Any

from dera.comparison.models import ComparisonReport
from dera.migration.planning.reports import MigrationPlanReport
from dera.migration.reports.models import MigrationRiskReport
from dera.migration.sql.reports import SqlMigrationArtifact
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dera_api.db.models.migration_artifacts import (
    MigrationComparisonRecord,
    MigrationExportRecord,
    MigrationPlanRecord,
    MigrationRiskRecord,
    MigrationSqlArtifactRecord,
)


class MigrationArtifactsRepository:
    """Repository handling durable CRUD for migration engineering artifacts."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- Comparisons ---

    async def save_comparison(
        self,
        workspace_id: uuid.UUID,
        report: ComparisonReport,
    ) -> MigrationComparisonRecord:
        """Persist schema comparison report."""
        record = MigrationComparisonRecord(
            workspace_id=workspace_id,
            report_id_str=report.report_id,
            baseline_snapshot_id=report.baseline_snapshot_id,
            target_snapshot_id=report.target_snapshot_id,
            baseline_fingerprint=report.baseline_fingerprint,
            target_fingerprint=report.target_fingerprint,
            report_fingerprint=report.report_fingerprint,
            engine=report.engine,
            target_engine=report.target_engine,
            status=report.status.value if hasattr(report.status, "value") else str(report.status),
            report_json=report.model_dump(mode="json"),
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_comparison(
        self,
        workspace_id: uuid.UUID,
        report_id: str,
    ) -> ComparisonReport | None:
        """Retrieve comparison report ensuring workspace boundary."""
        stmt = select(MigrationComparisonRecord).where(
            MigrationComparisonRecord.workspace_id == workspace_id,
            MigrationComparisonRecord.report_id_str == report_id,
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return None
        return ComparisonReport.model_validate(record.report_json)

    # --- Risk Reports ---

    async def save_risk_report(
        self,
        workspace_id: uuid.UUID,
        report: MigrationRiskReport,
    ) -> MigrationRiskRecord:
        """Persist migration risk assessment report."""
        record = MigrationRiskRecord(
            workspace_id=workspace_id,
            report_id_str=report.report_id,
            comparison_report_id=report.comparison_report_id,
            comparison_fingerprint=report.comparison_report_fingerprint,
            report_fingerprint=report.fingerprint,
            risk_level=report.overall_risk_level.value
            if hasattr(report.overall_risk_level, "value")
            else str(report.overall_risk_level),
            has_breaking_changes=report.has_breaking_changes,
            has_destructive_changes=report.has_destructive_changes,
            report_json=report.model_dump(mode="json"),
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_risk_report(
        self,
        workspace_id: uuid.UUID,
        report_id: str,
    ) -> MigrationRiskReport | None:
        """Retrieve risk report ensuring workspace boundary."""
        stmt = select(MigrationRiskRecord).where(
            MigrationRiskRecord.workspace_id == workspace_id,
            MigrationRiskRecord.report_id_str == report_id,
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return None
        return MigrationRiskReport.model_validate(record.report_json)

    # --- Migration Plans ---

    async def save_plan(
        self,
        workspace_id: uuid.UUID,
        plan: MigrationPlanReport,
    ) -> MigrationPlanRecord:
        """Persist migration plan report."""
        record = MigrationPlanRecord(
            workspace_id=workspace_id,
            plan_id_str=plan.plan_id,
            risk_report_id=plan.risk_report_id,
            risk_report_fingerprint=plan.risk_report_fingerprint,
            plan_fingerprint=plan.fingerprint,
            operation_count=len(plan.planned_operations),
            requires_manual_approval=plan.requires_manual_approval,
            plan_json=plan.model_dump(mode="json"),
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_plan(
        self,
        workspace_id: uuid.UUID,
        plan_id: str,
    ) -> MigrationPlanReport | None:
        """Retrieve migration plan ensuring workspace boundary."""
        stmt = select(MigrationPlanRecord).where(
            MigrationPlanRecord.workspace_id == workspace_id,
            MigrationPlanRecord.plan_id_str == plan_id,
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return None
        return MigrationPlanReport.model_validate(record.plan_json)

    # --- SQL Artifacts ---

    async def save_sql_artifact(
        self,
        workspace_id: uuid.UUID,
        artifact: SqlMigrationArtifact,
    ) -> MigrationSqlArtifactRecord:
        """Persist compiled SQL migration artifact."""
        rollback_sql = "\n\n".join(r.sql for r in artifact.rollback_statements)
        record = MigrationSqlArtifactRecord(
            workspace_id=workspace_id,
            artifact_id_str=artifact.artifact_id,
            plan_id=artifact.source_plan_id,
            plan_fingerprint=artifact.source_plan_fingerprint,
            target_dialect=artifact.dialect.value
            if hasattr(artifact.dialect, "value")
            else str(artifact.dialect),
            artifact_fingerprint=artifact.artifact_fingerprint,
            sql_content=artifact.rendered_sql_script,
            rollback_sql=rollback_sql if rollback_sql else None,
            artifact_json=artifact.model_dump(mode="json"),
        )
        self._session.add(record)
        await self._session.flush()
        return record

    async def get_sql_artifact(
        self,
        workspace_id: uuid.UUID,
        artifact_id: str,
    ) -> SqlMigrationArtifact | None:
        """Retrieve SQL artifact ensuring workspace boundary."""
        stmt = select(MigrationSqlArtifactRecord).where(
            MigrationSqlArtifactRecord.workspace_id == workspace_id,
            MigrationSqlArtifactRecord.artifact_id_str == artifact_id,
        )
        result = await self._session.execute(stmt)
        record = result.scalar_one_or_none()
        if not record:
            return None
        payload = dict(record.artifact_json)
        payload["artifact_fingerprint"] = record.artifact_fingerprint
        return SqlMigrationArtifact.model_validate(payload)

    # --- Exports ---

    async def save_export(
        self,
        workspace_id: uuid.UUID,
        export_pkg: dict[str, Any],
    ) -> MigrationExportRecord:
        """Persist authorized export record."""
        exported_at = export_pkg["exported_at"]
        if isinstance(exported_at, str):
            from datetime import datetime

            exported_at_dt = datetime.fromisoformat(exported_at)
        else:
            exported_at_dt = exported_at

        # Ensure package_json is strictly JSON-serializable (ISO-format timestamps)
        pkg_json = dict(export_pkg)
        if hasattr(pkg_json.get("exported_at"), "isoformat"):
            pkg_json["exported_at"] = pkg_json["exported_at"].isoformat()

        record = MigrationExportRecord(
            workspace_id=workspace_id,
            export_id_str=export_pkg["export_id"],
            review_id=export_pkg["review_id"],
            artifact_id=export_pkg["artifact_id"],
            artifact_fingerprint=export_pkg["artifact_fingerprint"],
            exported_by=export_pkg["exported_by"],
            exported_at=exported_at_dt,
            package_json=pkg_json,
        )
        self._session.add(record)
        await self._session.flush()
        return record
