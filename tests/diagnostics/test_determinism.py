"""Tests for DERA diagnostic determinism, input order insensitivity, and report reproducibility."""

from __future__ import annotations

import random
from dataclasses import dataclass

from dera.diagnostics.context import DiagnosticContext
from dera.diagnostics.evaluator import DiagnosticEvaluator
from dera.diagnostics.rules.foundational import (
    ALL_FOUNDATIONAL_RULES,
)
from dera.diagnostics.serialization import compute_report_content_hash


@dataclass
class SimpleCol:
    object_id: str
    name: str


@dataclass
class SimpleTable:
    object_id: str
    name: str
    columns: tuple[SimpleCol, ...] = ()
    indexes: tuple = ()
    constraints: tuple = ()


@dataclass
class SimpleFK:
    foreign_key_id: str
    foreign_key_name: str
    source_table_name: str
    referenced_table_name: str
    source_columns: tuple[str, ...]
    referenced_columns: tuple[str, ...]
    status: str = "resolved"


@dataclass
class SimpleSchema:
    tables: tuple[SimpleTable, ...]
    views: tuple = ()
    namespaces: tuple = ()
    foreign_key_references: tuple[SimpleFK, ...] = ()


def test_evaluator_input_order_insensitivity() -> None:
    """Verifies that reordering tables or rules in input produces equivalent report content hash."""
    t1 = SimpleTable(
        object_id="dera:table:1",
        name="table_a",
        columns=(SimpleCol("dera:col:1", "id"),),
    )
    t2 = SimpleTable(
        object_id="dera:table:2",
        name="table_b",
        columns=(),  # Produces finding for empty columns
    )
    t3 = SimpleTable(
        object_id="dera:table:3",
        name="table_c",
        columns=(SimpleCol("dera:col:3", "id"),),
    )

    fk1 = SimpleFK(
        foreign_key_id="fk_1",
        foreign_key_name="fk_1",
        source_table_name="table_a",
        referenced_table_name="missing_table_x",
        source_columns=("target_id",),
        referenced_columns=("id",),
        status="missing",  # Produces finding
    )

    schema_order_1 = SimpleSchema(
        tables=(t1, t2, t3),
        foreign_key_references=(fk1,),
    )
    schema_order_2 = SimpleSchema(
        tables=(t3, t1, t2),
        foreign_key_references=(fk1,),
    )

    evaluator = DiagnosticEvaluator()

    report_1 = evaluator.evaluate(
        DiagnosticContext(schema=schema_order_1),
        list(ALL_FOUNDATIONAL_RULES),
    )

    # Shuffle rules order to verify rule evaluation order stability
    shuffled_rules = list(ALL_FOUNDATIONAL_RULES)
    random.Random(42).shuffle(shuffled_rules)

    report_2 = evaluator.evaluate(
        DiagnosticContext(schema=schema_order_2),
        shuffled_rules,
    )

    # Finding fingerprints and order must match exactly
    fps1 = [f.fingerprint for f in report_1.findings]
    fps2 = [f.fingerprint for f in report_2.findings]
    assert fps1 == fps2

    # Content hashes must be strictly identical
    hash1 = compute_report_content_hash(report_1.to_canonical_dict())
    hash2 = compute_report_content_hash(report_2.to_canonical_dict())
    assert hash1 == hash2


def test_repeated_evaluation_identical_findings() -> None:
    """Verifies that evaluating the same context multiple times produces bit-for-bit identical hashes."""
    t = SimpleTable(
        object_id="dera:table:t1",
        name="test_table",
        columns=(),
    )
    schema = SimpleSchema(tables=(t,))
    evaluator = DiagnosticEvaluator()
    context = DiagnosticContext(schema=schema)

    report_a = evaluator.evaluate(context, list(ALL_FOUNDATIONAL_RULES))
    report_b = evaluator.evaluate(context, list(ALL_FOUNDATIONAL_RULES))

    assert report_a.report_hash == report_b.report_hash
    assert len(report_a.findings) == len(report_b.findings)
    assert [f.fingerprint for f in report_a.findings] == [f.fingerprint for f in report_b.findings]
