"""Tests for cycle breakability, nullable FK evaluation, and break strategy recommendation."""

from __future__ import annotations

from dera.reverse_engineering.dependencies.models import BreakabilityStrategy

from tests.reverse_engineering.phase_6_4.fixtures import (
    analyze_database,
    make_mutual_cycle_schema,
    make_self_referencing_schema,
)


def test_nullable_cycle_breakability():
    """Verify that a cycle with a nullable FK is marked breakable via NULLABLE_FOREIGN_KEY."""
    db = make_mutual_cycle_schema(author_nullable=True, book_nullable=False)
    res = analyze_database(db)

    assert res.cycle_report.cycle_count == 1
    cycle = res.cycle_report.cycles[0]
    assert cycle.is_breakable is True
    assert cycle.recommended_break_strategy == BreakabilityStrategy.NULLABLE_FOREIGN_KEY
    assert len(cycle.break_edges) >= 1


def test_deferrable_cycle_breakability():
    """Verify that a cycle with a deferrable FK is marked breakable via DEFERRABLE_CONSTRAINT."""
    db = make_mutual_cycle_schema(author_nullable=False, book_nullable=False, is_deferrable=True)
    res = analyze_database(db)

    assert res.cycle_report.cycle_count == 1
    cycle = res.cycle_report.cycles[0]
    assert cycle.is_breakable is True
    assert cycle.recommended_break_strategy == BreakabilityStrategy.DEFERRABLE_CONSTRAINT


def test_unbreakable_cycle_detection():
    """Verify that a cycle with non-nullable, non-deferrable FKs is marked UNBREAKABLE."""
    db = make_mutual_cycle_schema(author_nullable=False, book_nullable=False, is_deferrable=False)
    res = analyze_database(db)

    assert res.cycle_report.cycle_count == 1
    cycle = res.cycle_report.cycles[0]
    assert cycle.is_breakable is False
    assert cycle.recommended_break_strategy == BreakabilityStrategy.UNBREAKABLE
    assert len(cycle.break_edges) == 0
    assert res.cycle_report.unbreakable_cycle_count == 1


def test_self_referencing_breakability():
    """Verify self-referencing column nullability determines breakability."""
    db_nullable = make_self_referencing_schema(is_nullable=True)
    res_null = analyze_database(db_nullable)
    assert res_null.cycle_report.cycles[0].is_breakable is True

    db_not_null = make_self_referencing_schema(is_nullable=False)
    res_not_null = analyze_database(db_not_null)
    assert res_not_null.cycle_report.cycles[0].is_breakable is False
