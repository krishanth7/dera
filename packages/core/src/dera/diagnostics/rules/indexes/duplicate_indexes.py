"""DERA Diagnostics — Rule DERA-IDX-001: Exact Duplicate Index Definition.

Detects structurally equivalent database index definitions defined on the same table.
Preserves engine-specific semantics and identifies constraint-owned indexes.
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
from dera.diagnostics.rules.shared.index_signatures import (
    are_indexes_exactly_duplicate,
    is_constraint_owned_index,
)

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class DuplicateIndexesRule:
    """Detects duplicate index definitions on the same table."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-IDX-001",
            title="Exact Duplicate Index Definition",
            description=(
                "Detects two or more index definitions on the same table that share identical "
                "access methods, key terms, sort directions, NULL ordering, and partial predicates."
            ),
            version="1.0.0",
            category=RuleCategory.INDEXES,
            default_severity=DiagnosticSeverity.MEDIUM,
            supported_object_kinds=("table", "index"),
            required_capabilities=("indexes", "tables"),
            applicability_summary="Applies to all relational tables with multiple indexes.",
            evidence_requirements="Requires canonical index signatures, terms, and predicates.",
            recommendation_template=(
                "Review redundant index '{duplicate_index_name}' on table '{table_name}'. "
                "Evaluate dropping one duplicate after confirming no code relies specifically on its name."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-IDX-001",
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        start_time = time.perf_counter()
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
        detected_pairs: set[frozenset[str]] = set()

        sorted_tables = sorted(
            tables, key=lambda t: (getattr(t, "name", ""), str(getattr(t, "id", "")))
        )

        for table in sorted_tables:
            indexes = getattr(table, "indexes", ())
            if len(indexes) < 2:
                continue

            sorted_indexes = sorted(
                indexes,
                key=lambda idx: (getattr(idx, "name", ""), str(getattr(idx, "id", ""))),
            )

            for i in range(len(sorted_indexes)):
                for j in range(i + 1, len(sorted_indexes)):
                    idx1 = sorted_indexes[i]
                    idx2 = sorted_indexes[j]

                    id1 = str(getattr(idx1, "id", idx1.name))
                    id2 = str(getattr(idx2, "id", idx2.name))
                    pair_key = frozenset([id1, id2])
                    if pair_key in detected_pairs:
                        continue

                    is_dup, reason = are_indexes_exactly_duplicate(idx1, idx2)
                    if not is_dup:
                        continue

                    detected_pairs.add(pair_key)

                    is_owned1, owner_desc1 = is_constraint_owned_index(idx1, table)
                    is_owned2, owner_desc2 = is_constraint_owned_index(idx2, table)

                    terms1 = getattr(idx1, "terms", None)
                    if terms1:
                        cols_display = ", ".join(
                            f"'{t.column_name or t.expression}'" for t in terms1
                        )
                    else:
                        cols = getattr(idx1, "columns", None) or getattr(idx1, "column_names", ())
                        cols_display = ", ".join(f"'{c}'" for c in cols)

                    tbl_name = getattr(table, "name", "<unnamed_table>")
                    tbl_id = str(getattr(table, "id", tbl_name))

                    evidence = (
                        DiagnosticEvidence(
                            object_id=id2,
                            field_name="index_definition",
                            observed_value=reason,
                            expected_value="Distinct index definition",
                            message=(
                                f"Index '{idx2.name}' duplicates '{idx1.name}' on table '{tbl_name}' ({cols_display})."
                            ),
                            context_data={
                                "table_id": tbl_id,
                                "table_name": tbl_name,
                                "primary_index_id": id1,
                                "primary_index_name": idx1.name,
                                "duplicate_index_id": id2,
                                "duplicate_index_name": idx2.name,
                                "primary_ownership": owner_desc1,
                                "duplicate_ownership": owner_desc2,
                                "indexed_terms": cols_display,
                            },
                        ),
                    )

                    rec_suffix = ""
                    if is_owned1 or is_owned2:
                        rec_suffix = (
                            f" Note: {owner_desc1 if is_owned1 else ''} "
                            f"{owner_desc2 if is_owned2 else ''}. "
                            "Do not drop constraint-owned indexes directly; modify the declaring constraint instead."
                        )

                    findings.append(
                        DiagnosticFinding(
                            rule_id=self.metadata.rule_id,
                            rule_version=self.metadata.version,
                            object_id=id2,
                            severity=self.metadata.default_severity,
                            title=f"Duplicate index definition: {tbl_name}.{idx2.name}",
                            description=(
                                f"Table '{tbl_name}' contains duplicate indexes '{idx1.name}' and '{idx2.name}'. "
                                f"{reason}."
                            ),
                            evidence=evidence,
                            severity_rationale=(
                                "Exact duplicate indexes consume storage, increase write amplification on INSERT/UPDATE/DELETE, "
                                "and provide no additional query optimization benefit."
                            ),
                            recommendation=(
                                f"Review indexes '{idx1.name}' and '{idx2.name}'. Consider dropping '{idx2.name}'."
                                + rec_suffix
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
                message=f"Detected {len(findings)} exact duplicate index definitions.",
            )

        return RuleEvaluation(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            status=EvaluationStatus.PASS,
            findings=(),
            execution_duration_ms=elapsed,
            message="No duplicate index definitions found.",
        )
