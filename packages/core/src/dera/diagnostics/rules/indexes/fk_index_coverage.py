"""DERA Diagnostics — Rule DERA-IDX-003: Foreign Key Supporting Index Coverage.

Identifies foreign keys whose referencing columns lack supporting index
coverage with the foreign key columns as a leading prefix in relational engines
that do not automatically index foreign keys (e.g. PostgreSQL, SQLite).
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from dera.diagnostics.enums import (
    DiagnosticSeverity,
    EvaluationStatus,
    RuleCategory,
)
from dera.diagnostics.evidence import DiagnosticEvidence
from dera.diagnostics.models import (
    DiagnosticFinding,
    RuleEvaluation,
    RuleMetadata,
)
from dera.diagnostics.rules.shared.capability_checks import (
    engine_automatically_indexes_foreign_keys,
    normalize_engine_name,
)

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class FkIndexCoverageRule:
    """Evaluates whether referencing foreign key columns have supporting index coverage."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-IDX-003",
            title="Foreign Key Supporting Index Coverage",
            description=(
                "Detects foreign key constraints whose referencing child columns lack a supporting "
                "leading-prefix index in database engines that do not automatically index foreign keys."
            ),
            version="1.0.0",
            category=RuleCategory.INDEXES,
            default_severity=DiagnosticSeverity.MEDIUM,
            supported_object_kinds=("foreign_key", "table"),
            required_capabilities=("foreign_keys", "indexes"),
            applicability_summary="Applies to PostgreSQL, SQLite, and engines without automatic FK indexing.",
            evidence_requirements="Requires foreign key child columns and table index definitions.",
            recommendation_template=(
                "Consider creating an index on table '{table_name}' with leading columns ({columns}) "
                "to optimize joins and cascade operations."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-IDX-003",
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        start_time = time.perf_counter()
        engine = normalize_engine_name(
            getattr(context, "engine", getattr(context, "source_engine", "unknown"))
        )

        # Check engine automatic indexing behavior
        if engine_automatically_indexes_foreign_keys(engine):
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.NOT_APPLICABLE,
                findings=(),
                execution_duration_ms=(time.perf_counter() - start_time) * 1000,
                message=f"Engine '{engine}' automatically indexes foreign key columns (InnoDB).",
            )

        schema = context.schema
        if schema is None and context.snapshot is not None:
            schema = getattr(context.snapshot, "schema_representation", None)

        if schema is None:
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.INSUFFICIENT_METADATA,
                findings=(),
                execution_duration_ms=(time.perf_counter() - start_time) * 1000,
                message="No schema representation available in diagnostic context.",
            )

        tables = getattr(schema, "tables", ())
        if not tables:
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.PASS,
                findings=(),
                execution_duration_ms=(time.perf_counter() - start_time) * 1000,
                message="No tables present in schema.",
            )

        findings: list[DiagnosticFinding] = []
        sorted_tables = sorted(
            tables, key=lambda t: (getattr(t, "name", ""), str(getattr(t, "id", "")))
        )

        for table in sorted_tables:
            table_name = getattr(table, "name", "<unnamed_table>")
            table_id = str(getattr(table, "id", table_name))
            table_indexes = getattr(table, "indexes", ())
            table_fks = getattr(table, "foreign_keys", ())

            sorted_fks = sorted(
                table_fks,
                key=lambda fk: (getattr(fk, "name", "") or "", str(getattr(fk, "id", ""))),
            )

            for fk in sorted_fks:
                fk_cols = list(
                    getattr(fk, "source_columns", None)
                    or getattr(fk, "constrained_columns", None)
                    or getattr(fk, "column_names", ())
                )
                if not fk_cols:
                    continue

                fk_name = getattr(fk, "name", "unnamed_fk")
                fk_id = str(getattr(fk, "id", f"{table_id}.{fk_name}"))
                ref_table = (
                    getattr(fk, "referenced_table_name", None)
                    or getattr(fk, "referred_table", None)
                    or getattr(fk, "target_table", "")
                )

                has_supporting_index = False
                candidate_partial_indexes: list[str] = []

                for idx in table_indexes:
                    idx_terms = getattr(idx, "terms", None)
                    if idx_terms:
                        idx_cols = [t.column_name for t in idx_terms if t.column_name]
                    else:
                        idx_cols = list(
                            getattr(idx, "columns", None) or getattr(idx, "column_names", ())
                        )

                    if len(idx_cols) >= len(fk_cols) and idx_cols[: len(fk_cols)] == fk_cols:
                        if getattr(idx, "predicate", None):
                            candidate_partial_indexes.append(getattr(idx, "name", "unnamed_idx"))
                        else:
                            has_supporting_index = True
                            break

                if not has_supporting_index:
                    cols_str = ", ".join(fk_cols)
                    evidence = (
                        DiagnosticEvidence(
                            object_id=fk_id,
                            field_name="fk_index_coverage",
                            observed_value="No non-partial leading-prefix index",
                            expected_value=f"Index with leading prefix ({cols_str})",
                            message=(
                                f"Foreign key '{fk_name}' on table '{table_name}' ({cols_str}) "
                                "lacks a supporting non-partial leading-prefix index."
                            ),
                            context_data={
                                "table_id": table_id,
                                "table_name": table_name,
                                "foreign_key_id": fk_id,
                                "foreign_key_name": fk_name,
                                "foreign_key_columns": fk_cols,
                                "referenced_table": ref_table,
                                "candidate_partial_indexes": candidate_partial_indexes,
                                "existing_indexes": [getattr(i, "name", "") for i in table_indexes],
                                "engine": engine,
                            },
                        ),
                    )

                    findings.append(
                        DiagnosticFinding(
                            rule_id=self.metadata.rule_id,
                            rule_version=self.metadata.version,
                            object_id=fk_id,
                            severity=self.metadata.default_severity,
                            title=f"Unindexed foreign key: {table_name}.{fk_name}",
                            description=(
                                f"Foreign key '{fk_name}' on table '{table_name}' referencing '{ref_table}' "
                                f"has no supporting leading-prefix index on ({cols_str})."
                            ),
                            evidence=evidence,
                            severity_rationale=(
                                "In engines like PostgreSQL and SQLite, unindexed foreign keys can cause sequential "
                                "table scans on parent table updates and deletes, potentially degrading performance."
                            ),
                            recommendation=(
                                f"Consider adding an index on '{table_name}' with leading columns ({cols_str}) "
                                "if this relationship is frequently joined or updated on the parent table."
                            ),
                        )
                    )

        elapsed = (time.perf_counter() - start_time) * 1000

        if findings:
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.FINDINGS_DETECTED,
                findings=tuple(findings),
                execution_duration_ms=elapsed,
                message=f"Detected {len(findings)} unindexed foreign keys.",
            )

        return RuleEvaluation(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            status=EvaluationStatus.PASS,
            findings=(),
            execution_duration_ms=elapsed,
            message="All foreign keys have supporting leading-prefix index coverage.",
        )
