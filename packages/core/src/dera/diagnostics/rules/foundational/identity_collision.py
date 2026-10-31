"""DERA Diagnostics — Rule DERA-SCHEMA-002: Canonical Identity Collision.

Detects duplicate canonical object identifiers across schema collections,
identifying internal normalization defects or collision integrity violations.
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

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext


class CanonicalIdentityCollisionRule:
    """Detects duplicate canonical ObjectIds across database objects."""

    def __init__(self) -> None:
        self._metadata = RuleMetadata(
            rule_id="DERA-SCHEMA-002",
            title="Canonical Object Identity Collision",
            description=(
                "Detects duplicate canonical ObjectIds across registered schema entities. "
                "Such collisions indicate internal normalization or inspection integrity issues."
            ),
            version="1.0.0",
            category=RuleCategory.STRUCTURAL_INTEGRITY,
            default_severity=DiagnosticSeverity.CRITICAL,
            supported_object_kinds=("table", "view", "column", "constraint", "index"),
            required_capabilities=(),
            applicability_summary="Applies to all inspected schema representations.",
            evidence_requirements="Requires canonical ObjectIds and entity native names.",
            recommendation_template=(
                "Review the canonical identity generation algorithm and connector normalization pipeline "
                "for object '{object_name}' to resolve the collision."
            ),
            documentation_url="https://docs.dera.dev/diagnostics/rules/DERA-SCHEMA-002",
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

        seen_identities: dict[str, str] = {}  # object_id -> object descriptor
        collisions: list[tuple[str, str, str]] = []  # (object_id, desc1, desc2)

        # Collect objects from tables, views, namespaces, columns
        objects_to_check: list[tuple[str, str]] = []

        for ns in getattr(schema, "namespaces", ()):
            ns_id = getattr(ns, "object_id", None)
            ns_name = getattr(ns, "name", "<unnamed_namespace>")
            if ns_id:
                objects_to_check.append((ns_id, f"Namespace: {ns_name}"))

        for tbl in getattr(schema, "tables", ()):
            tbl_id = getattr(tbl, "object_id", None)
            tbl_name = getattr(tbl, "name", "<unnamed_table>")
            if tbl_id:
                objects_to_check.append((tbl_id, f"Table: {tbl_name}"))

            for col in getattr(tbl, "columns", ()):
                col_id = getattr(col, "object_id", None)
                col_name = getattr(col, "name", "<unnamed_column>")
                if col_id:
                    objects_to_check.append((col_id, f"Column: {tbl_name}.{col_name}"))

            for idx in getattr(tbl, "indexes", ()):
                idx_id = getattr(idx, "object_id", None)
                idx_name = getattr(idx, "name", "<unnamed_index>")
                if idx_id:
                    objects_to_check.append((idx_id, f"Index: {tbl_name}.{idx_name}"))

            for cst in getattr(tbl, "constraints", ()):
                cst_id = getattr(cst, "object_id", None)
                cst_name = getattr(cst, "name", "<unnamed_constraint>")
                if cst_id:
                    objects_to_check.append((cst_id, f"Constraint: {tbl_name}.{cst_name}"))

        for vw in getattr(schema, "views", ()):
            vw_id = getattr(vw, "object_id", None)
            vw_name = getattr(vw, "name", "<unnamed_view>")
            if vw_id:
                objects_to_check.append((vw_id, f"View: {vw_name}"))

        for obj_id, desc in objects_to_check:
            if obj_id in seen_identities:
                prev_desc = seen_identities[obj_id]
                # If they are distinct entities sharing the same object_id
                if prev_desc != desc:
                    collisions.append((obj_id, prev_desc, desc))
            else:
                seen_identities[obj_id] = desc

        findings: list[DiagnosticFinding] = []
        for obj_id, first_entity, second_entity in collisions:
            evidence = (
                DiagnosticEvidence(
                    object_id=obj_id,
                    field_name="object_id",
                    observed_value=f"Shared by '{first_entity}' and '{second_entity}'",
                    expected_value="Globally unique canonical ObjectId",
                    message=(
                        f"Canonical identity collision detected: '{first_entity}' and "
                        f"'{second_entity}' both produced ObjectId '{obj_id}'."
                    ),
                    context_data={
                        "first_entity": first_entity,
                        "second_entity": second_entity,
                    },
                ),
            )

            finding = DiagnosticFinding(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                object_id=obj_id,
                severity=self.metadata.default_severity,
                title="Duplicate canonical ObjectId detected",
                description=(
                    f"Two distinct schema entities ('{first_entity}' and '{second_entity}') "
                    f"share the canonical ObjectId '{obj_id}'."
                ),
                evidence=evidence,
                severity_rationale=(
                    "Canonical ObjectIds must be strictly unique to maintain registry consistency, "
                    "graph integrity, and immutable snapshot reproducibility. Collisions indicate "
                    "an internal normalization flaw rather than a customer schema error."
                ),
                recommendation=self.metadata.recommendation_template.format(
                    object_name=second_entity
                ),
            )
            findings.append(finding)

        elapsed = (time.perf_counter() - start_time) * 1000

        if findings:
            return RuleEvaluation(
                rule_id=self.metadata.rule_id,
                rule_version=self.metadata.version,
                status=EvaluationStatus.FINDINGS_DETECTED,
                findings=tuple(findings),
                execution_duration_ms=elapsed,
                message=f"Detected {len(findings)} canonical identity collisions.",
            )

        return RuleEvaluation(
            rule_id=self.metadata.rule_id,
            rule_version=self.metadata.version,
            status=EvaluationStatus.PASS,
            findings=(),
            execution_duration_ms=elapsed,
            message="No canonical identity collisions detected across registered objects.",
        )
