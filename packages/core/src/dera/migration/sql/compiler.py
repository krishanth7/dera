"""Migration SQL Compiler Engine.

Translates verified Phase 9.3 MigrationPlanReport plans into reviewable SQL artifacts:
1. Validates plan consistency and blocking status.
2. Resolves dialect renderer via DialectRegistry.
3. Translates each ordered abstract operation into dialect-specific SQL statements.
4. Preserves dependency order and stage sequencing.
5. Plans transaction blocks (transactional vs non-transactional DDL).
6. Runs offline structural and dialect syntax validation.
7. Aggregates preflight checks and rollback statements.
8. Produces canonical SHA-256 artifact fingerprint and reviewable SqlMigrationArtifact.
"""

from dera.migration.planning.enums import PlanStatus
from dera.migration.planning.reports import MigrationPlanReport
from dera.migration.sql.enums import SqlDialectType, SqlGenerationStatus
from dera.migration.sql.fingerprint import SqlFingerprintCalculator
from dera.migration.sql.models import (
    GeneratedSqlStatement,
    PreflightCheck,
    RollbackStatement,
    TransactionBlock,
)
from dera.migration.sql.registry import DialectRegistry
from dera.migration.sql.reports import SqlArtifactSummary, SqlMigrationArtifact
from dera.migration.sql.transaction_planner import TransactionPlanner
from dera.migration.sql.validation import SqlValidator


class SqlMigrationCompiler:
    """Deterministic dialect-aware SQL migration compiler."""

    COMPILER_VERSION = "1.0.0"

    def __init__(self, default_dialect: SqlDialectType | None = None):
        self.default_dialect = default_dialect

    def compile_plan(
        self,
        plan_report: MigrationPlanReport,
        target_engine: str | None = None,
        target_version: str | None = None,
        allow_partial: bool = False,
    ) -> SqlMigrationArtifact:
        """Compile a Phase 9.3 migration plan into a reviewable SQL artifact."""
        engine = (target_engine or plan_report.target_engine).lower()
        dialect_type = DialectRegistry.map_to_dialect_type(engine)
        renderer = DialectRegistry.get_renderer(engine)

        # 1. Plan status verification
        if (
            plan_report.plan_status in (PlanStatus.BLOCKED, PlanStatus.UNSUPPORTED)
            and not allow_partial
        ):
            status = (
                SqlGenerationStatus.BLOCKED
                if plan_report.plan_status == PlanStatus.BLOCKED
                else SqlGenerationStatus.UNSUPPORTED
            )
            return self._build_empty_artifact(
                plan_report=plan_report,
                dialect=dialect_type,
                engine=engine,
                status=status,
                reason=f"Plan status is {plan_report.plan_status.value}. Script generation aborted to prevent partial/unsafe execution.",
            )

        # 2. Compile operations into statements in plan order
        statements: list[GeneratedSqlStatement] = []
        for op in plan_report.operations:
            rendered_stmts = renderer.render_operation(op, target_version=target_version)
            statements.extend(rendered_stmts)

        # 3. Transaction planning
        transaction_blocks = TransactionPlanner.plan_transactions(statements, dialect_type)

        # 4. Offline structural validation
        is_valid, validation_issues = SqlValidator.validate_statements(statements, dialect_type)

        # 5. Extract preflights and rollbacks
        preflight_checks: list[PreflightCheck] = []
        rollback_statements: list[RollbackStatement] = []
        destructive_count = 0
        review_required_count = 0

        for stmt in statements:
            if stmt.is_destructive:
                destructive_count += 1
            if stmt.requires_manual_review:
                review_required_count += 1
            preflight_checks.extend(stmt.preflight_checks)
            if stmt.rollback_statement:
                rollback_statements.append(stmt.rollback_statement)

        # 6. Render full SQL script
        rendered_script = self._render_full_script(
            transaction_blocks=transaction_blocks,
            dialect=dialect_type,
            plan_report=plan_report,
        )

        # 7. Summary metrics
        summary = SqlArtifactSummary(
            total_statements=len(statements),
            destructive_statements=destructive_count,
            review_required_statements=review_required_count,
            transaction_blocks_count=len(transaction_blocks),
            preflight_checks_count=len(preflight_checks),
            rollback_statements_count=len(rollback_statements),
            validation_issues_count=len(validation_issues),
        )

        # 8. Generation status derivation
        if not is_valid:
            status = SqlGenerationStatus.VALIDATION_FAILED
        elif (
            review_required_count > 0
            or plan_report.plan_status == PlanStatus.REQUIRES_MANUAL_DECISION
        ):
            status = SqlGenerationStatus.GENERATED_WITH_REVIEW_REQUIRED
        else:
            status = SqlGenerationStatus.GENERATED

        # 9. Compute artifact fingerprint
        fingerprint = SqlFingerprintCalculator.compute_artifact_fingerprint(
            source_plan_fingerprint=plan_report.plan_fingerprint,
            dialect=dialect_type,
            compiler_version=self.COMPILER_VERSION,
            statements=statements,
            transaction_blocks=transaction_blocks,
        )

        artifact_id = f"art_sql_{fingerprint[:16]}"

        return SqlMigrationArtifact(
            artifact_id=artifact_id,
            source_plan_id=plan_report.plan_id,
            source_plan_fingerprint=plan_report.plan_fingerprint,
            source_risk_report_fingerprint=plan_report.risk_report_fingerprint,
            dialect=dialect_type,
            target_engine=engine,
            compiler_version=self.COMPILER_VERSION,
            status=status,
            artifact_fingerprint=fingerprint,
            summary=summary,
            rendered_sql_script=rendered_script,
            statements=statements,
            transaction_blocks=transaction_blocks,
            preflight_checks=preflight_checks,
            rollback_statements=rollback_statements,
            validation_issues=validation_issues,
            limitations=[
                "SQL statements are generated for offline human engineering review.",
                "Automatic execution against live databases is strictly prohibited.",
            ],
        )

    def _render_full_script(
        self,
        transaction_blocks: list[TransactionBlock],
        dialect: SqlDialectType,
        plan_report: MigrationPlanReport,
    ) -> str:
        header = [
            "-- ============================================================================",
            "-- DERA MIGRATION SQL ARTIFACT",
            f"-- Dialect: {dialect.value}",
            f"-- Source Plan: {plan_report.plan_id}",
            f"-- Baseline: {plan_report.baseline_snapshot_id} -> Target: {plan_report.target_snapshot_id}",
            "-- STATUS: GENERATED FOR REVIEW — NOT EXECUTED",
            "-- ============================================================================\n",
        ]

        body = [block.rendered_block_sql for block in transaction_blocks]
        return "\n".join(header) + "\n\n".join(body) + "\n"

    def _build_empty_artifact(
        self,
        plan_report: MigrationPlanReport,
        dialect: SqlDialectType,
        engine: str,
        status: SqlGenerationStatus,
        reason: str,
    ) -> SqlMigrationArtifact:
        fingerprint = SqlFingerprintCalculator.compute_artifact_fingerprint(
            source_plan_fingerprint=plan_report.plan_fingerprint,
            dialect=dialect,
            compiler_version=self.COMPILER_VERSION,
            statements=[],
            transaction_blocks=[],
        )
        return SqlMigrationArtifact(
            artifact_id=f"art_sql_{fingerprint[:16]}",
            source_plan_id=plan_report.plan_id,
            source_plan_fingerprint=plan_report.plan_fingerprint,
            source_risk_report_fingerprint=plan_report.risk_report_fingerprint,
            dialect=dialect,
            target_engine=engine,
            compiler_version=self.COMPILER_VERSION,
            status=status,
            artifact_fingerprint=fingerprint,
            summary=SqlArtifactSummary(
                total_statements=0,
                destructive_statements=0,
                review_required_statements=0,
                transaction_blocks_count=0,
                preflight_checks_count=0,
                rollback_statements_count=0,
                validation_issues_count=0,
            ),
            rendered_sql_script=f"-- GENERATION BLOCKED: {reason}\n",
            statements=[],
            transaction_blocks=[],
            preflight_checks=[],
            rollback_statements=[],
            validation_issues=[],
            limitations=[reason],
        )
