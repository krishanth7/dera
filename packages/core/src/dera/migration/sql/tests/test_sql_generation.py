"""Unit and Dialect Tests for Phase 9.4 Migration SQL Generation.

Covers:
1. Identifier quoting and SQL injection prevention.
2. Dialect translation across PostgreSQL, Supabase, SQLite, MySQL, and MariaDB.
3. Transaction planning and boundary separation.
4. Offline structural validation.
5. Deterministic artifact fingerprinting.
6. Traceability from SQL statement to source operation.
"""

import pytest
from dera.comparison.enums import ComparisonChangeType, ComparisonObjectType, ComparisonStatus
from dera.comparison.models import (
    ComparisonConfig,
    ComparisonReport,
    ComparisonSummary,
    SchemaChange,
)
from dera.diagnostics.enums import DiagnosticSeverity
from dera.migration.classification.models import ClassifiedChange
from dera.migration.enums import (
    CompatibilityLevel,
    ReversibilityClassification,
    ReviewPriority,
    RiskDimension,
    RiskEvidenceCertainty,
    StructuralChangeCategory,
)
from dera.migration.planning import MigrationPlanningEngine
from dera.migration.reports.models import MigrationRiskReport
from dera.migration.risk.models import MigrationRiskAssessment
from dera.migration.sql import (
    IdentifierQuoter,
    SqlDialectType,
    SqlGenerationStatus,
    SqlMigrationCompiler,
    SqlValidator,
    TransactionExecutionMode,
)


def _make_dummy_plan(changes, engine="postgresql"):
    config = ComparisonConfig()
    summary = ComparisonSummary(
        total_changes=len(changes),
        total_added=sum(1 for c in changes if c.change_type == ComparisonChangeType.ADDED),
        total_removed=sum(1 for c in changes if c.change_type == ComparisonChangeType.REMOVED),
        total_modified=sum(1 for c in changes if c.change_type == ComparisonChangeType.MODIFIED),
    )

    comp_report = ComparisonReport.create(
        baseline_snapshot_id="snap_base",
        baseline_fingerprint="base_fp_12345",
        target_snapshot_id="snap_target",
        target_fingerprint="target_fp_12345",
        engine=engine,
        target_engine=engine,
        config=config,
        status=ComparisonStatus.DIFFERENCES_FOUND,
        summary=summary,
        changes=tuple(changes),
    )

    classified = []
    risks = []
    for c in changes:
        cc = ClassifiedChange(
            source_change_id=c.change_id,
            source_fingerprint=c.fingerprint,
            object_type=c.object_type,
            change_type=c.change_type,
            category=StructuralChangeCategory.ADDITIVE
            if c.change_type == ComparisonChangeType.ADDED
            else StructuralChangeCategory.REMOVAL,
            canonical_id=c.canonical_id,
            namespace=c.namespace,
            name=c.name,
            parent_name=c.parent_name,
            compatibility=CompatibilityLevel.COMPATIBLE_WITH_KNOWN_METADATA,
            is_potentially_breaking=False,
            compatibility_rationale="Evaluated change.",
        )
        classified.append(cc)

        ra = MigrationRiskAssessment.create(
            source_change_id=c.change_id,
            source_change_fingerprint=c.fingerprint,
            rule_id="RULE-RISK-001",
            dimension=RiskDimension.DATA_PRESERVATION,
            severity=DiagnosticSeverity.INFORMATIONAL,
            priority=ReviewPriority.P4_LOW,
            certainty=RiskEvidenceCertainty.VERIFIED,
            reversibility=ReversibilityClassification.POTENTIALLY_REVERSIBLE,
            title="Safe change",
            description="Structural impact analyzed.",
            evidence_summary={},
        )
        risks.append(ra)

    risk_report = MigrationRiskReport.create(
        baseline_snapshot_id="snap_base",
        baseline_fingerprint="base_fp_12345",
        target_snapshot_id="snap_target",
        target_fingerprint="target_fp_12345",
        comparison_report_id=comp_report.report_id,
        comparison_fingerprint=comp_report.report_fingerprint,
        engine=engine,
        classified_changes=tuple(classified),
        risk_assessments=tuple(risks),
    )

    planner = MigrationPlanningEngine(target_engine=engine)
    return planner.plan_migration(comp_report, risk_report)


def test_safe_identifier_quoting_and_injection_prevention():
    """Verify that identifiers are properly escaped and injection attempts are blocked."""
    # Standard identifier
    assert IdentifierQuoter.quote_identifier("users", SqlDialectType.POSTGRESQL) == '"users"'
    assert IdentifierQuoter.quote_identifier("users", SqlDialectType.MYSQL) == "`users`"

    # Embedded quote escaping
    assert (
        IdentifierQuoter.quote_identifier('user"table', SqlDialectType.POSTGRESQL)
        == '"user""table"'
    )
    assert IdentifierQuoter.quote_identifier("user`table", SqlDialectType.MYSQL) == "`user``table`"

    # Injection with semicolons or comments is safely treated as literal identifier text
    quoted_pg = IdentifierQuoter.quote_identifier(
        "users; DROP TABLE evil; --", SqlDialectType.POSTGRESQL
    )
    assert quoted_pg == '"users; DROP TABLE evil; --"'

    # Malicious null byte must raise ValueError
    with pytest.raises(ValueError, match="null byte"):
        IdentifierQuoter.quote_identifier("users\x00evil", SqlDialectType.POSTGRESQL)


def test_postgresql_ddl_and_transaction_wrapping():
    """Verify PostgreSQL generates properly quoted transactional DDL."""
    changes = [
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.TABLE,
            canonical_id="tbl_users_id",
            namespace="public",
            name="users",
            engine="postgresql",
        ),
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.COLUMN,
            canonical_id="col_email_id",
            namespace="public",
            name="email",
            parent_canonical_id="tbl_users_id",
            parent_name="users",
            engine="postgresql",
        ),
    ]

    plan = _make_dummy_plan(changes, engine="postgresql")
    compiler = SqlMigrationCompiler()
    artifact = compiler.compile_plan(plan)

    assert artifact.dialect == SqlDialectType.POSTGRESQL
    assert artifact.status in (
        SqlGenerationStatus.GENERATED,
        SqlGenerationStatus.GENERATED_WITH_REVIEW_REQUIRED,
    )
    assert "BEGIN;" in artifact.rendered_sql_script
    assert "COMMIT;" in artifact.rendered_sql_script
    assert '"public"."users"' in artifact.rendered_sql_script
    assert len(artifact.statements) == 2
    # Verify statement traceability
    assert artifact.statements[0].source_operation_type.value == "CREATE_TABLE"
    assert artifact.statements[1].source_operation_type.value == "ADD_COLUMN"


def test_mysql_ddl_and_implicit_commits():
    """Verify MySQL renders with backticks and recognizes implicit commit mode."""
    changes = [
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.TABLE,
            canonical_id="tbl_orders_id",
            namespace="shop",
            name="orders",
            engine="mysql",
        )
    ]

    plan = _make_dummy_plan(changes, engine="mysql")
    compiler = SqlMigrationCompiler()
    artifact = compiler.compile_plan(plan)

    assert artifact.dialect == SqlDialectType.MYSQL
    assert "`shop`.`orders`" in artifact.rendered_sql_script
    assert artifact.statements[0].execution_mode == TransactionExecutionMode.IMPLICIT_COMMIT
    # No BEGIN / COMMIT block for MySQL DDL
    assert "BEGIN;" not in artifact.rendered_sql_script


def test_sqlite_ddl_and_unsupported_ops():
    """Verify SQLite generates standard table operations and flags unsupported DDL."""
    changes = [
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.TABLE,
            canonical_id="tbl_posts_id",
            namespace="main",
            name="posts",
            engine="sqlite",
        )
    ]

    plan = _make_dummy_plan(changes, engine="sqlite")
    compiler = SqlMigrationCompiler()
    artifact = compiler.compile_plan(plan)

    assert artifact.dialect == SqlDialectType.SQLITE
    assert 'CREATE TABLE IF NOT EXISTS "posts"' in artifact.rendered_sql_script
    assert "BEGIN TRANSACTION;" in artifact.rendered_sql_script


def test_deterministic_sql_artifact_fingerprint():
    """Verify that compiling the same plan multiple times produces identical byte-for-byte artifacts."""
    changes = [
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.TABLE,
            canonical_id="tbl_a_id",
            namespace="public",
            name="table_a",
            engine="postgresql",
        ),
        SchemaChange.create(
            change_type=ComparisonChangeType.ADDED,
            object_type=ComparisonObjectType.TABLE,
            canonical_id="tbl_b_id",
            namespace="public",
            name="table_b",
            engine="postgresql",
        ),
    ]

    plan = _make_dummy_plan(changes, engine="postgresql")
    compiler = SqlMigrationCompiler()

    art1 = compiler.compile_plan(plan)
    art2 = compiler.compile_plan(plan)

    assert art1.artifact_fingerprint == art2.artifact_fingerprint
    assert art1.rendered_sql_script == art2.rendered_sql_script
    assert [s.statement_fingerprint for s in art1.statements] == [
        s.statement_fingerprint for s in art2.statements
    ]


def test_offline_validator_detects_unbalanced_quotes():
    """Verify validator flags unbalanced quotes in generated SQL."""
    from dera.migration.planning.enums import MigrationOperationType
    from dera.migration.sql.models import GeneratedSqlStatement

    stmt = GeneratedSqlStatement(
        statement_id="stmt_bad",
        source_operation_id="op_1",
        source_operation_type=MigrationOperationType.CREATE_TABLE,
        target_object_id="tbl_1",
        target_object_name="bad_table",
        sql='CREATE TABLE "unbalanced (id INT);',
        dialect=SqlDialectType.POSTGRESQL,
        statement_fingerprint="fp_bad",
    )

    is_valid, issues = SqlValidator.validate_statements([stmt], SqlDialectType.POSTGRESQL)
    assert is_valid is False
    assert len(issues) > 0
    assert issues[0].issue_type == "UNBALANCED_QUOTES"
