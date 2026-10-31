"""Tests for DERA diagnostic evaluation against immutable Phase 6.5 snapshots."""

from __future__ import annotations

from dera.diagnostics.context import DiagnosticContext
from dera.diagnostics.evaluator import DiagnosticEvaluator
from dera.diagnostics.rules.foundational import ALL_FOUNDATIONAL_RULES
from dera.reverse_engineering.builder import SchemaBuilder

from tests.reverse_engineering.phase_6_5.fixtures import (
    build_snapshot_from_database,
    make_composite_constraints_database,
)


def test_diagnostics_from_immutable_snapshot() -> None:
    """Verifies evaluating diagnostic rules directly against an immutable SchemaSnapshot."""
    canonical_db = make_composite_constraints_database()
    schema = SchemaBuilder.from_canonical_database(canonical_db)

    # Build Phase 6.5 immutable snapshot using verified pipeline helper
    snapshot = build_snapshot_from_database(canonical_db, workspace_id="ws_snapshot_test")

    evaluator = DiagnosticEvaluator()
    context = DiagnosticContext(
        snapshot=snapshot,
        snapshot_id=snapshot.snapshot_id,
        schema=schema,
    )

    report = evaluator.evaluate(context, list(ALL_FOUNDATIONAL_RULES))

    assert report.snapshot_id == snapshot.snapshot_id
    assert report.summary.rules_errored == 0
    assert report.summary.total_rules_evaluated > 0


def test_snapshot_diagnostic_hash_reproducibility() -> None:
    """Verifies that running diagnostics twice on the same snapshot produces identical report hashes."""
    canonical_db = make_composite_constraints_database()
    schema = SchemaBuilder.from_canonical_database(canonical_db)
    snapshot = build_snapshot_from_database(canonical_db, workspace_id="ws_repro_test")

    evaluator = DiagnosticEvaluator()
    context1 = DiagnosticContext(snapshot=snapshot, snapshot_id=snapshot.snapshot_id, schema=schema)
    context2 = DiagnosticContext(snapshot=snapshot, snapshot_id=snapshot.snapshot_id, schema=schema)

    rep1 = evaluator.evaluate(context1, list(ALL_FOUNDATIONAL_RULES))
    rep2 = evaluator.evaluate(context2, list(ALL_FOUNDATIONAL_RULES))

    assert rep1.report_hash == rep2.report_hash
    assert [f.fingerprint for f in rep1.findings] == [f.fingerprint for f in rep2.findings]
