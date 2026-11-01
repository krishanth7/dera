"""DERA Migration — Phase 9.2 Risk Evaluator Engine.

Evaluates classified schema changes against deterministic risk rules:
1. Data Preservation: Table/Column drops, type narrowing
2. Constraint Safety: Nullability enforcement, PK changes, new unique/FK/check constraints
3. Operational & Locking: Postgres/MySQL online DDL caveats, SQLite table rebuilds
4. Dependency Blast Radius: Downstream cascades on dropped/modified parents
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera.comparison.enums import ComparisonChangeType, ComparisonObjectType
from dera.diagnostics.enums import DiagnosticSeverity
from dera.migration.classification.models import ClassifiedChange
from dera.migration.enums import (
    ReversibilityClassification,
    ReviewPriority,
    RiskDimension,
    RiskEvidenceCertainty,
)
from dera.migration.impact.blast_radius import BlastRadiusMetrics
from dera.migration.recommendations.models import EngineeringRecommendation
from dera.migration.risk.models import MigrationRiskAssessment

if TYPE_CHECKING:
    from dera.comparison.models import SchemaChange


class RiskEvaluator:
    """Evaluates classified changes to produce explainable MigrationRiskAssessments."""

    @classmethod
    def evaluate_change_risks(
        cls,
        classified: ClassifiedChange,
        raw_change: SchemaChange,
        blast_radius: BlastRadiusMetrics | None = None,
        engine: str = "postgresql",
    ) -> list[MigrationRiskAssessment]:
        """Generate all applicable risk assessments for a single schema change."""
        risks: list[MigrationRiskAssessment] = []

        # 1. Dropped Table
        if (
            classified.object_type == ComparisonObjectType.TABLE
            and classified.change_type == ComparisonChangeType.REMOVED
        ):
            risks.append(cls._evaluate_dropped_table(classified, raw_change, blast_radius))

        # 2. Dropped Column
        elif (
            classified.object_type == ComparisonObjectType.COLUMN
            and classified.change_type == ComparisonChangeType.REMOVED
        ):
            risks.append(cls._evaluate_dropped_column(classified, raw_change))

        # 3. New Non-Null Column
        elif (
            classified.object_type == ComparisonObjectType.COLUMN
            and classified.change_type == ComparisonChangeType.ADDED
        ):
            risk = cls._evaluate_added_column(classified, raw_change, engine)
            if risk:
                risks.append(risk)

        # 4. Modified Column (Nullability & Type Narrowing)
        elif (
            classified.object_type == ComparisonObjectType.COLUMN
            and classified.change_type == ComparisonChangeType.MODIFIED
        ):
            risks.extend(cls._evaluate_modified_column(classified, raw_change, engine))

        # 5. Primary Key Modifications
        elif classified.object_type == ComparisonObjectType.PRIMARY_KEY:
            risks.append(cls._evaluate_primary_key(classified, raw_change))

        # 6. New Constraints (Unique, FK, Check)
        elif classified.object_type in (
            ComparisonObjectType.UNIQUE_CONSTRAINT,
            ComparisonObjectType.FOREIGN_KEY,
            ComparisonObjectType.CHECK_CONSTRAINT,
        ) and classified.change_type == ComparisonChangeType.ADDED:
            risks.append(cls._evaluate_added_constraint(classified, raw_change))

        # 7. Dropped Index
        elif (
            classified.object_type == ComparisonObjectType.INDEX
            and classified.change_type == ComparisonChangeType.REMOVED
        ):
            risks.append(cls._evaluate_dropped_index(classified, raw_change))

        # 8. Dependency Blast Radius Risks
        if blast_radius and blast_radius.direct_dependents_count > 0:
            if classified.change_type == ComparisonChangeType.REMOVED:
                risks.append(cls._evaluate_dependency_blast_radius(classified, blast_radius))

        return risks

    @staticmethod
    def _evaluate_dropped_table(
        classified: ClassifiedChange,
        raw_change: SchemaChange,
        blast_radius: BlastRadiusMetrics | None,
    ) -> MigrationRiskAssessment:
        recs = (
            EngineeringRecommendation(
                recommendation_id=f"rec_drop_tbl_{classified.name}",
                risk_id="",
                title="Verify data backup and archival before dropping table",
                description=f"Export table '{classified.name}' data to long-term storage or verify zero active reads.",
                rationale="Dropping a table permanently destroys all resident tuples and dependent objects.",
                suggested_review_actions=(
                    "Verify query logs for references to the table in the last 30 days.",
                    "Take a point-in-time snapshot or logical dump prior to running migration DDL.",
                ),
            ),
        )
        return MigrationRiskAssessment.create(
            source_change_id=classified.source_change_id,
            source_change_fingerprint=classified.source_fingerprint,
            rule_id="RISK-DATA-001",
            dimension=RiskDimension.DATA_PRESERVATION,
            severity=DiagnosticSeverity.CRITICAL,
            priority=ReviewPriority.P1_CRITICAL,
            certainty=RiskEvidenceCertainty.CONDITIONAL,
            reversibility=ReversibilityClassification.REQUIRES_PRESERVED_DATA,
            title=f"Potential data loss from dropping table '{classified.name}'",
            description=(
                f"Table '{classified.name}' in namespace '{classified.namespace}' is removed. "
                "Execution of this change will permanently destroy all contained rows and indexes."
            ),
            evidence_summary={
                "table_name": classified.name,
                "namespace": classified.namespace,
                "change_type": "REMOVED",
            },
            assumptions=("Table may contain production data; data cannot be recovered without backup.",),
            limitations=("Schema metadata cannot determine row count or customer table traffic.",),
            recommendations=recs,
        )

    @staticmethod
    def _evaluate_dropped_column(
        classified: ClassifiedChange,
        raw_change: SchemaChange,
    ) -> MigrationRiskAssessment:
        recs = (
            EngineeringRecommendation(
                recommendation_id=f"rec_drop_col_{classified.name}",
                risk_id="",
                title="Verify application code references before dropping column",
                description=f"Ensure no active application queries or ORM models select or write to '{classified.name}'.",
                rationale="Dropping a column immediately fails SELECT * or explicit queries referencing the column.",
                suggested_review_actions=(
                    "Deprecate column in application code prior to dropping from schema.",
                    "Verify zero active application releases still query this column.",
                ),
            ),
        )
        return MigrationRiskAssessment.create(
            source_change_id=classified.source_change_id,
            source_change_fingerprint=classified.source_fingerprint,
            rule_id="RISK-DATA-002",
            dimension=RiskDimension.DATA_PRESERVATION,
            severity=DiagnosticSeverity.HIGH,
            priority=ReviewPriority.P2_HIGH,
            certainty=RiskEvidenceCertainty.CONDITIONAL,
            reversibility=ReversibilityClassification.REQUIRES_PRESERVED_DATA,
            title=f"Potential data loss from dropping column '{classified.name}'",
            description=(
                f"Column '{classified.name}' on table '{classified.parent_name}' is removed. "
                "Values in this column will be discarded upon migration execution."
            ),
            evidence_summary={
                "column_name": classified.name,
                "table_name": classified.parent_name,
            },
            assumptions=("Column contains populated historical data.",),
            limitations=("Database metadata alone cannot verify external application code references.",),
            recommendations=recs,
        )

    @staticmethod
    def _evaluate_added_column(
        classified: ClassifiedChange,
        raw_change: SchemaChange,
        engine: str,
    ) -> MigrationRiskAssessment | None:
        after_props = raw_change.after_evidence.properties if raw_change.after_evidence else {}
        is_nullable = after_props.get("is_nullable", True)
        default_expr = after_props.get("default_expression")

        if not is_nullable and default_expr is None:
            recs = (
                EngineeringRecommendation(
                    recommendation_id=f"rec_add_col_nn_{classified.name}",
                    risk_id="",
                    title="Provide default value or multi-phase backfill for NOT NULL column",
                    description=f"Add column '{classified.name}' as nullable first, backfill data, then alter to NOT NULL.",
                    rationale="Adding a NOT NULL column without a default to a populated table fails migration execution.",
                    suggested_review_actions=(
                        "Phase 1: ADD COLUMN nullable.",
                        "Phase 2: Backfill existing rows in bounded batches.",
                        "Phase 3: ALTER COLUMN SET NOT NULL.",
                    ),
                ),
            )
            return MigrationRiskAssessment.create(
                source_change_id=classified.source_change_id,
                source_change_fingerprint=classified.source_fingerprint,
                rule_id="RISK-COMPAT-001",
                dimension=RiskDimension.MIGRATION_EXECUTION_COMPLEXITY,
                severity=DiagnosticSeverity.HIGH,
                priority=ReviewPriority.P2_HIGH,
                certainty=RiskEvidenceCertainty.VERIFIED,
                reversibility=ReversibilityClassification.POTENTIALLY_REVERSIBLE,
                title=f"Non-nullable column '{classified.name}' added without default value",
                description=(
                    f"Column '{classified.name}' on '{classified.parent_name}' is NOT NULL and lacks a default expression. "
                    "If the target table contains rows, migration execution will immediately abort."
                ),
                evidence_summary={
                    "is_nullable": is_nullable,
                    "default_expression": default_expr,
                },
                assumptions=("Target table may contain existing records.",),
                recommendations=recs,
            )
        return None

    @classmethod
    def _evaluate_modified_column(
        cls,
        classified: ClassifiedChange,
        raw_change: SchemaChange,
        engine: str,
    ) -> list[MigrationRiskAssessment]:
        risks: list[MigrationRiskAssessment] = []
        prop_diffs = {p.property_name: p for p in raw_change.property_differences}

        # Nullability enforcement
        if "is_nullable" in prop_diffs:
            diff = prop_diffs["is_nullable"]
            if diff.before_value is True and diff.after_value is False:
                recs = (
                    EngineeringRecommendation(
                        recommendation_id=f"rec_nn_enforce_{classified.name}",
                        risk_id="",
                        title="Audit table for NULL values before enforcing NOT NULL",
                        description=f"Run SELECT COUNT(*) WHERE {classified.name} IS NULL prior to applying NOT NULL.",
                        rationale="Enforcing NOT NULL fails if any existing tuple contains a NULL value.",
                        suggested_review_actions=(
                            f"SELECT COUNT(*) FROM {classified.parent_name} WHERE {classified.name} IS NULL;",
                            "Backfill any null occurrences with valid placeholder values.",
                        ),
                    ),
                )
                risks.append(
                    MigrationRiskAssessment.create(
                        source_change_id=classified.source_change_id,
                        source_change_fingerprint=classified.source_fingerprint,
                        rule_id="RISK-COMPAT-002",
                        dimension=RiskDimension.DATA_PRESERVATION,
                        severity=DiagnosticSeverity.HIGH,
                        priority=ReviewPriority.P2_HIGH,
                        certainty=RiskEvidenceCertainty.CONDITIONAL,
                        reversibility=ReversibilityClassification.POTENTIALLY_REVERSIBLE,
                        title=f"Enforcing NOT NULL on column '{classified.name}'",
                        description=(
                            f"Column '{classified.name}' changed from nullable to non-nullable. "
                            "Existing rows containing NULL will trigger constraint violations."
                        ),
                        evidence_summary={"before_nullable": True, "after_nullable": False},
                        assumptions=("Existing rows may contain NULL values.",),
                        recommendations=recs,
                    )
                )

        # Type narrowing
        if "native_data_type" in prop_diffs:
            diff = prop_diffs["native_data_type"]
            recs = (
                EngineeringRecommendation(
                    recommendation_id=f"rec_type_narrow_{classified.name}",
                    risk_id="",
                    title="Validate existing values fit new data type constraints",
                    description=f"Verify no values in '{classified.name}' exceed destination range or format.",
                    rationale="Altering column data type risks numeric overflow or string truncation.",
                    suggested_review_actions=(
                        "Inspect maximum string length or numeric value ranges in source data.",
                        "Test conversion in staging replica before production rollout.",
                    ),
                ),
            )
            risks.append(
                MigrationRiskAssessment.create(
                    source_change_id=classified.source_change_id,
                    source_change_fingerprint=classified.source_fingerprint,
                    rule_id="RISK-DATA-003",
                    dimension=RiskDimension.DATA_PRESERVATION,
                    severity=DiagnosticSeverity.HIGH,
                    priority=ReviewPriority.P2_HIGH,
                    certainty=RiskEvidenceCertainty.CONDITIONAL,
                    reversibility=ReversibilityClassification.REQUIRES_PRESERVED_DATA,
                    title=f"Type alteration on column '{classified.name}'",
                    description=(
                        f"Data type altered from '{diff.before_value}' to '{diff.after_value}'. "
                        "May require explicit type cast or table rewrite depending on engine."
                    ),
                    evidence_summary={
                        "before_type": diff.before_value,
                        "after_type": diff.after_value,
                    },
                    assumptions=("Data conversion may truncate or fail on incompatible values.",),
                    recommendations=recs,
                )
            )

        return risks

    @staticmethod
    def _evaluate_primary_key(
        classified: ClassifiedChange,
        raw_change: SchemaChange,
    ) -> MigrationRiskAssessment:
        recs = (
            EngineeringRecommendation(
                recommendation_id=f"rec_pk_mod_{classified.name}",
                risk_id="",
                title="Verify ORM and foreign-key dependencies before altering Primary Key",
                description=f"Primary key '{classified.name}' on '{classified.parent_name}' altered.",
                rationale="Changing a primary key invalidates foreign-key relationships and ORM identity assumptions.",
                suggested_review_actions=(
                    "Check foreign keys referencing this primary key.",
                    "Audit ORM models and unique indexing strategies.",
                ),
            ),
        )
        return MigrationRiskAssessment.create(
            source_change_id=classified.source_change_id,
            source_change_fingerprint=classified.source_fingerprint,
            rule_id="RISK-COMPAT-003",
            dimension=RiskDimension.SCHEMA_COMPATIBILITY,
            severity=DiagnosticSeverity.CRITICAL,
            priority=ReviewPriority.P1_CRITICAL,
            certainty=RiskEvidenceCertainty.VERIFIED,
            reversibility=ReversibilityClassification.REVERSIBLE_UNDER_STATED_CONDITIONS,
            title=f"Primary Key alteration on table '{classified.parent_name}'",
            description=f"Primary key '{classified.name}' definition was modified or removed.",
            evidence_summary={"primary_key": classified.name, "table": classified.parent_name},
            recommendations=recs,
        )

    @staticmethod
    def _evaluate_added_constraint(
        classified: ClassifiedChange,
        raw_change: SchemaChange,
    ) -> MigrationRiskAssessment:
        recs = (
            EngineeringRecommendation(
                recommendation_id=f"rec_add_con_{classified.name}",
                risk_id="",
                title="Validate existing rows satisfy new constraint condition",
                description=f"Verify data before adding {classified.object_type.value} '{classified.name}'.",
                rationale="Adding a constraint validates existing data; invalid rows abort migration.",
                suggested_review_actions=(
                    "Run validation queries on target table before applying DDL.",
                    "In PostgreSQL, consider adding constraint NOT VALID then validating separately.",
                ),
            ),
        )
        return MigrationRiskAssessment.create(
            source_change_id=classified.source_change_id,
            source_change_fingerprint=classified.source_fingerprint,
            rule_id="RISK-COMPAT-004",
            dimension=RiskDimension.MIGRATION_EXECUTION_COMPLEXITY,
            severity=DiagnosticSeverity.MEDIUM,
            priority=ReviewPriority.P3_MEDIUM,
            certainty=RiskEvidenceCertainty.CONDITIONAL,
            reversibility=ReversibilityClassification.POTENTIALLY_REVERSIBLE,
            title=f"New constraint '{classified.name}' requires data validation",
            description=f"Adding {classified.object_type.value} '{classified.name}' may require table scanning and validation locks.",
            evidence_summary={"constraint_name": classified.name},
            recommendations=recs,
        )

    @staticmethod
    def _evaluate_dropped_index(
        classified: ClassifiedChange,
        raw_change: SchemaChange,
    ) -> MigrationRiskAssessment:
        recs = (
            EngineeringRecommendation(
                recommendation_id=f"rec_drop_idx_{classified.name}",
                risk_id="",
                title="Audit query workload before dropping index",
                description=f"Confirm index '{classified.name}' is unused in production query execution plans.",
                rationale="Dropping an index may cause queries to fall back to sequential table scans.",
                suggested_review_actions=(
                    "Check pg_stat_user_indexes or performance schema for index scans.",
                ),
            ),
        )
        return MigrationRiskAssessment.create(
            source_change_id=classified.source_change_id,
            source_change_fingerprint=classified.source_fingerprint,
            rule_id="RISK-PERF-001",
            dimension=RiskDimension.OPERATIONAL_AVAILABILITY,
            severity=DiagnosticSeverity.LOW,
            priority=ReviewPriority.P4_LOW,
            certainty=RiskEvidenceCertainty.CONDITIONAL,
            reversibility=ReversibilityClassification.POTENTIALLY_REVERSIBLE,
            title=f"Index '{classified.name}' dropped",
            description=f"Dropping index '{classified.name}' on '{classified.parent_name}' may affect query execution plans.",
            evidence_summary={"index_name": classified.name, "parent_table": classified.parent_name},
            recommendations=recs,
        )

    @staticmethod
    def _evaluate_dependency_blast_radius(
        classified: ClassifiedChange,
        blast_radius: BlastRadiusMetrics,
    ) -> MigrationRiskAssessment:
        recs = (
            EngineeringRecommendation(
                recommendation_id=f"rec_blast_{classified.name}",
                risk_id="",
                title="Cascade impact review for dependent tables",
                description=f"Dropping '{classified.name}' affects {blast_radius.direct_dependents_count} referencing child tables.",
                rationale="Downstream tables holding foreign keys will have constraints broken or rejected.",
                suggested_review_actions=(
                    "Drop or update referencing foreign keys before removing parent table.",
                ),
            ),
        )
        return MigrationRiskAssessment.create(
            source_change_id=classified.source_change_id,
            source_change_fingerprint=classified.source_fingerprint,
            rule_id="RISK-BLAST-001",
            dimension=RiskDimension.DEPENDENCY_IMPACT,
            severity=DiagnosticSeverity.HIGH,
            priority=ReviewPriority.P1_CRITICAL,
            certainty=RiskEvidenceCertainty.VERIFIED,
            reversibility=ReversibilityClassification.REQUIRES_PRESERVED_DATA,
            title=f"High blast radius: '{classified.name}' has {blast_radius.direct_dependents_count} dependent tables",
            description=(
                f"Removing table '{classified.name}' impacts {blast_radius.direct_dependents_count} direct dependents "
                f"and {blast_radius.transitive_dependents_count} transitive dependents across namespaces: "
                f"{', '.join(blast_radius.affected_namespaces)}."
            ),
            evidence_summary={
                "direct_dependents": blast_radius.direct_dependents_count,
                "transitive_dependents": blast_radius.transitive_dependents_count,
                "max_depth": blast_radius.max_dependency_depth,
            },
            recommendations=recs,
        )
