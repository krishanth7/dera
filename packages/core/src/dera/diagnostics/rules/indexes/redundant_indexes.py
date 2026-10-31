"""DERA Diagnostics — Rule DERA-IDX-002: Potentially Redundant B-Tree Index.

Detects B-Tree indexes whose key columns form a strict leftmost prefix of a wider
composite B-Tree index on the same table.
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
    is_btree_leftmost_prefix,
    is_constraint_owned_index,
)

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class RedundantIndexesRule:
    """Detects B-Tree indexes that may be redundant due to wider composite prefixes."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-IDX-002",
            title="Potentially Redundant B-Tree Index (Leftmost Prefix)",
            description=(
                "Identifies B-Tree indexes whose key terms are a strict leftmost prefix of a wider "
                "composite B-Tree index on the same table. Reports them conservatively as review candidates."
            ),
            version="1.0.0",
            category=RuleCategory.INDEXES,
            default_severity=DiagnosticSeverity.LOW,
            supported_object_kinds=("table", "index"),
            required_capabilities=("indexes", "tables"),
            applicability_summary="Applies to B-Tree indexes on relational tables.",
            evidence_requirements="Requires canonical index signatures, access method, and term order.",
            recommendation_template=(
                "Review narrow index '{narrow_index_name}' against composite index '{wide_index_name}'. "
                "Inspect query access patterns and planner usage before deciding to drop."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-IDX-002",
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
        evaluated_pairs: set[frozenset[str]] = set()

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
                for j in range(len(sorted_indexes)):
                    if i == j:
                        continue
                    narrow_idx = sorted_indexes[i]
                    wide_idx = sorted_indexes[j]

                    id_n = str(getattr(narrow_idx, "id", narrow_idx.name))
                    id_w = str(getattr(wide_idx, "id", wide_idx.name))
                    pair_key = frozenset([id_n, id_w])
                    if pair_key in evaluated_pairs:
                        continue

                    is_prefix, reason = is_btree_leftmost_prefix(narrow_idx, wide_idx)
                    if not is_prefix:
                        continue

                    evaluated_pairs.add(pair_key)

                    is_owned_n, owner_desc_n = is_constraint_owned_index(narrow_idx, table)
                    is_owned_w, owner_desc_w = is_constraint_owned_index(wide_idx, table)

                    tbl_name = getattr(table, "name", "<unnamed_table>")
                    tbl_id = str(getattr(table, "id", tbl_name))

                    evidence = (
                        DiagnosticEvidence(
                            object_id=id_n,
                            field_name="leftmost_prefix",
                            observed_value=reason,
                            expected_value="Independent index term prefix",
                            message=(
                                f"Index '{narrow_idx.name}' is a strict prefix of wider index '{wide_idx.name}' "
                                f"on table '{tbl_name}'."
                            ),
                            context_data={
                                "table_id": tbl_id,
                                "table_name": tbl_name,
                                "narrow_index_id": id_n,
                                "narrow_index_name": narrow_idx.name,
                                "wide_index_id": id_w,
                                "wide_index_name": wide_idx.name,
                                "narrow_ownership": owner_desc_n,
                                "wide_ownership": owner_desc_w,
                                "relationship": reason,
                            },
                        ),
                    )

                    rec_suffix = ""
                    if is_owned_n:
                        rec_suffix = (
                            f" Note: {narrow_idx.name} {owner_desc_n}. "
                            "Do not drop constraint-owned indexes directly."
                        )

                    findings.append(
                        DiagnosticFinding(
                            rule_id=self.metadata.rule_id,
                            rule_version=self.metadata.version,
                            object_id=id_n,
                            severity=self.metadata.default_severity,
                            title=f"Potentially redundant index: {tbl_name}.{narrow_idx.name}",
                            description=(
                                f"Index '{narrow_idx.name}' on '{tbl_name}' is a leftmost prefix of '{wide_idx.name}'. "
                                "It may be a candidate for consolidation or removal depending on query workload."
                            ),
                            evidence=evidence,
                            severity_rationale=(
                                "Leftmost prefix indexes may duplicate lookup capability already provided by wider composite indexes, "
                                "but cannot be conclusively deprecated without analyzing production query plans, index sizes, and scan costs."
                            ),
                            recommendation=(
                                f"Review whether queries utilizing '{narrow_idx.name}' can efficiently use '{wide_idx.name}' instead."
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
                message=f"Detected {len(findings)} potentially redundant leftmost prefix indexes.",
            )

        return RuleEvaluation(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            status=EvaluationStatus.PASS,
            findings=(),
            execution_duration_ms=elapsed,
            message="No redundant leftmost prefix indexes detected.",
        )
