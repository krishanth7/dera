"""Unit tests for Phase 8.2 canonical index and constraint signature helpers."""

from __future__ import annotations

from dataclasses import dataclass, field

from dera.diagnostics.rules.shared.capability_checks import (
    engine_automatically_indexes_foreign_keys,
    engine_supports_check_constraints,
    engine_supports_expression_indexes,
    engine_supports_partial_indexes,
    normalize_engine_name,
)
from dera.diagnostics.rules.shared.constraint_signatures import (
    validate_column_references_exist,
)
from dera.diagnostics.rules.shared.index_signatures import (
    are_indexes_exactly_duplicate,
    compute_index_signature,
    is_btree_leftmost_prefix,
    is_constraint_owned_index,
)


@dataclass
class MockTerm:
    column_name: str | None = None
    expression: str | None = None
    ordinal_position: int = 1
    is_descending: bool = False
    nulls_first: bool = False
    is_expression: bool = False


@dataclass
class MockIndex:
    name: str
    id: str = "idx_id"
    parent_table_id: str = "tbl_id"
    is_unique: bool = False
    is_primary: bool = False
    index_type: str = "BTREE"
    terms: tuple[MockTerm, ...] = ()
    predicate: str | None = None


@dataclass
class MockColumn:
    name: str


@dataclass
class MockPK:
    name: str = "pk"
    columns: tuple[str, ...] = ()


@dataclass
class MockUQ:
    name: str = "uq"
    id: str = "uq_id"
    columns: tuple[str, ...] = ()


@dataclass
class MockTable:
    name: str
    id: str = "tbl_id"
    columns: tuple[MockColumn, ...] = field(default_factory=tuple)
    primary_key: MockPK | None = None
    unique_constraints: tuple[MockUQ, ...] = field(default_factory=tuple)


def test_index_signature_deterministic_hash() -> None:
    idx1 = MockIndex(
        name="idx_test",
        id="i1",
        terms=(MockTerm(column_name="col_a", ordinal_position=1),),
    )
    idx2 = MockIndex(
        name="idx_other_name",
        id="i2",
        terms=(MockTerm(column_name="col_a", ordinal_position=1),),
    )
    sig1 = compute_index_signature(idx1)
    sig2 = compute_index_signature(idx2)

    assert sig1.signature_hash() == sig2.signature_hash()


def test_are_indexes_exactly_duplicate() -> None:
    idx1 = MockIndex(
        name="idx1",
        id="i1",
        terms=(MockTerm(column_name="email", ordinal_position=1),),
    )
    idx2 = MockIndex(
        name="idx2",
        id="i2",
        terms=(MockTerm(column_name="email", ordinal_position=1),),
    )
    is_dup, reason = are_indexes_exactly_duplicate(idx1, idx2)
    assert is_dup is True
    assert "Identical BTREE" in reason


def test_is_btree_leftmost_prefix() -> None:
    narrow = MockIndex(
        name="idx_narrow",
        id="i1",
        terms=(MockTerm(column_name="tenant_id", ordinal_position=1),),
    )
    wide = MockIndex(
        name="idx_wide",
        id="i2",
        terms=(
            MockTerm(column_name="tenant_id", ordinal_position=1),
            MockTerm(column_name="user_id", ordinal_position=2),
        ),
    )
    is_prefix, reason = is_btree_leftmost_prefix(narrow, wide)
    assert is_prefix is True
    assert "strict leading prefix" in reason


def test_is_constraint_owned_index() -> None:
    table = MockTable(
        name="users",
        primary_key=MockPK(name="pk_users", columns=("id",)),
        unique_constraints=(MockUQ(name="uq_email", columns=("email",)),),
    )
    pk_idx = MockIndex(
        name="idx_pk",
        terms=(MockTerm(column_name="id", ordinal_position=1),),
    )
    uq_idx = MockIndex(
        name="idx_uq",
        terms=(MockTerm(column_name="email", ordinal_position=1),),
    )
    sec_idx = MockIndex(
        name="idx_sec",
        terms=(MockTerm(column_name="created_at", ordinal_position=1),),
    )

    owned_pk, desc_pk = is_constraint_owned_index(pk_idx, table)
    assert owned_pk is True
    assert "PRIMARY KEY" in desc_pk

    owned_uq, desc_uq = is_constraint_owned_index(uq_idx, table)
    assert owned_uq is True
    assert "UNIQUE" in desc_uq

    owned_sec, _ = is_constraint_owned_index(sec_idx, table)
    assert owned_sec is False


def test_validate_column_references_exist() -> None:
    table = MockTable(
        name="items",
        columns=(MockColumn(name="id"), MockColumn(name="sku")),
    )
    valid, missing = validate_column_references_exist(table, ("id", "sku"))
    assert valid is True
    assert missing == ()

    invalid, missing_cols = validate_column_references_exist(table, ("id", "price"))
    assert invalid is False
    assert missing_cols == ("price",)


def test_engine_capability_matrix() -> None:
    assert normalize_engine_name("postgresql") == "postgresql"
    assert normalize_engine_name("Supabase Postgres") == "postgresql"
    assert normalize_engine_name("SQLite 3.39") == "sqlite"
    assert normalize_engine_name("MySQL 8.0") == "mysql"
    assert normalize_engine_name("MariaDB 10.5") == "mariadb"

    assert engine_automatically_indexes_foreign_keys("mysql") is True
    assert engine_automatically_indexes_foreign_keys("mariadb") is True
    assert engine_automatically_indexes_foreign_keys("postgresql") is False
    assert engine_automatically_indexes_foreign_keys("sqlite") is False

    assert engine_supports_partial_indexes("postgresql") is True
    assert engine_supports_partial_indexes("sqlite") is True
    assert engine_supports_partial_indexes("mysql") is False

    assert engine_supports_expression_indexes("postgresql") is True
    assert engine_supports_check_constraints("postgresql") is True
