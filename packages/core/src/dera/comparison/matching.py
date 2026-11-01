"""DERA Comparison — Phase 9.1 Canonical Object Matching.

Matches schema objects between baseline and target snapshots using deterministic
canonical keys (ObjectId, namespace + name, or parent + constraint attributes).

Invariants:
- Objects are never matched by unstable display names or fuzzy heuristic guesses.
- A removed object and an added object are never conflated as a rename.
- Safe O(1) indexed dictionary lookups for high performance on large schemas.
"""

from __future__ import annotations

from typing import TypeVar

from dera.reverse_engineering.snapshots.models import (
    SnapshotCheckConstraintPayload,
    SnapshotColumnPayload,
    SnapshotForeignKeyPayload,
    SnapshotIndexPayload,
    SnapshotPrimaryKeyPayload,
    SnapshotRelationshipPayload,
    SnapshotTablePayload,
    SnapshotTriggerPayload,
    SnapshotUniqueConstraintPayload,
    SnapshotViewPayload,
)

T = TypeVar("T")


class ObjectMatch[T]:
    """Pair of matched objects from baseline and target snapshots."""

    __slots__ = ("key", "baseline", "target")

    def __init__(self, key: str, baseline: T | None, target: T | None) -> None:
        self.key = key
        self.baseline = baseline
        self.target = target

    @property
    def is_added(self) -> bool:
        return self.baseline is None and self.target is not None

    @property
    def is_removed(self) -> bool:
        return self.baseline is not None and self.target is None

    @property
    def is_both(self) -> bool:
        return self.baseline is not None and self.target is not None


def match_by_key[T](
    baseline_items: tuple[T, ...] | list[T],
    target_items: tuple[T, ...] | list[T],
    key_fn: callable,
) -> list[ObjectMatch[T]]:
    """Match items between two collections using a deterministic key function.

    Preserves stable ordering: baseline items first in original order,
    followed by target-only additions in target order.
    """
    baseline_map: dict[str, T] = {}
    for item in baseline_items:
        k = key_fn(item)
        baseline_map[k] = item

    target_map: dict[str, T] = {}
    for item in target_items:
        k = key_fn(item)
        target_map[k] = item

    matches: list[ObjectMatch[T]] = []
    seen_keys: set[str] = set()

    # Process baseline items (matched or removed)
    for k, b_item in baseline_map.items():
        t_item = target_map.get(k)
        matches.append(ObjectMatch(k, b_item, t_item))
        seen_keys.add(k)

    # Process added target items
    for k, t_item in target_map.items():
        if k not in seen_keys:
            matches.append(ObjectMatch(k, None, t_item))
            seen_keys.add(k)

    return matches


# Key extraction functions
def table_canonical_key(table: SnapshotTablePayload) -> str:
    """Canonical key for a table: namespace.table_name."""
    return f"{table.namespace}.{table.name}"


def column_canonical_key(column: SnapshotColumnPayload) -> str:
    """Canonical key for a column: column name (scoped within table)."""
    return column.name


def primary_key_canonical_key(pk: SnapshotPrimaryKeyPayload) -> str:
    """Canonical key for a primary key constraint."""
    return pk.name or "PRIMARY_KEY"


def foreign_key_canonical_key(fk: SnapshotForeignKeyPayload) -> str:
    """Canonical key for a foreign key constraint."""
    # Use constraint name if available; fall back to ordered source columns
    if fk.name:
        return fk.name
    cols = ",".join(fk.source_columns)
    return f"fk_cols_{cols}"


def unique_constraint_canonical_key(uc: SnapshotUniqueConstraintPayload) -> str:
    """Canonical key for a unique constraint."""
    if uc.name:
        return uc.name
    cols = ",".join(uc.columns)
    return f"unq_cols_{cols}"


def check_constraint_canonical_key(chk: SnapshotCheckConstraintPayload) -> str:
    """Canonical key for a check constraint."""
    return chk.name or f"chk_{chk.expression[:32]}"


def index_canonical_key(idx: SnapshotIndexPayload) -> str:
    """Canonical key for an index."""
    return idx.name


def view_canonical_key(view: SnapshotViewPayload) -> str:
    """Canonical key for a view: namespace.view_name."""
    return f"{view.namespace}.{view.name}"


def trigger_canonical_key(trig: SnapshotTriggerPayload) -> str:
    """Canonical key for a trigger: namespace.trigger_name."""
    return f"{trig.namespace}.{trig.name}"


def relationship_canonical_key(rel: SnapshotRelationshipPayload) -> str:
    """Canonical key for a relationship edge."""
    return rel.edge_id or f"{rel.source_table_id}->{rel.target_table_id}:{rel.constraint_name}"
