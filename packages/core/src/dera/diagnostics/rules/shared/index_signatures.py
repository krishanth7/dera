"""Canonical index signatures and structural equivalence utilities.

Provides deterministic index signature generation, exact duplicate verification,
leftmost-prefix B-Tree redundancy analysis, and constraint ownership inspection.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class CanonicalIndexTermSignature:
    """Normalized signature of an individual index term."""

    term_identifier: str
    ordinal_position: int
    is_descending: bool
    nulls_first: bool
    is_expression: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "term": self.term_identifier,
            "ordinal": self.ordinal_position,
            "desc": self.is_descending,
            "nulls_first": self.nulls_first,
            "expr": self.is_expression,
        }


def normalize_predicate(predicate: str | None) -> str | None:
    """Normalizes whitespace in partial index predicates while preserving literal case."""
    if not predicate:
        return None
    return " ".join(predicate.strip().split())


@dataclass(frozen=True)
class CanonicalIndexSignature:
    """Cryptographic and semantic signature of a database index."""

    parent_table_id: str
    index_type: str
    is_unique: bool
    terms: tuple[CanonicalIndexTermSignature, ...]
    predicate: str | None

    def signature_hash(self) -> str:
        """Deterministic SHA-256 fingerprint of semantic index attributes."""
        canonical_dict = {
            "table_id": self.parent_table_id,
            "type": self.index_type.lower(),
            "unique": self.is_unique,
            "terms": [t.to_dict() for t in self.terms],
            "predicate": normalize_predicate(self.predicate),
        }
        serialized = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_index_signature(index: Any) -> CanonicalIndexSignature:
    """Computes a canonical normalized signature for an index."""
    norm_terms: list[CanonicalIndexTermSignature] = []

    # If index has terms tuple
    terms = getattr(index, "terms", None)
    if terms:
        for term in sorted(terms, key=lambda t: getattr(t, "ordinal_position", 0)):
            if getattr(term, "is_expression", False) and getattr(term, "expression", None):
                ident = str(term.expression).strip().lower()
            elif getattr(term, "column_name", None):
                ident = str(term.column_name).strip().lower()
            else:
                ident = f"expr_ordinal_{getattr(term, 'ordinal_position', 1)}"

            norm_terms.append(
                CanonicalIndexTermSignature(
                    term_identifier=ident,
                    ordinal_position=getattr(term, "ordinal_position", 1),
                    is_descending=bool(getattr(term, "is_descending", False)),
                    nulls_first=bool(getattr(term, "nulls_first", False)),
                    is_expression=bool(getattr(term, "is_expression", False)),
                )
            )
    else:
        # Fallback to index.columns or index.column_names
        cols = getattr(index, "columns", None) or getattr(index, "column_names", ())
        for i, col in enumerate(cols):
            norm_terms.append(
                CanonicalIndexTermSignature(
                    term_identifier=str(col).strip().lower(),
                    ordinal_position=i + 1,
                    is_descending=False,
                    nulls_first=False,
                    is_expression=False,
                )
            )

    idx_type_attr = getattr(index, "index_type", "BTREE")
    idx_type_val = (
        idx_type_attr.value if hasattr(idx_type_attr, "value") else str(idx_type_attr)
    ).lower()

    table_id = getattr(index, "parent_table_id", getattr(index, "table_id", "default_table"))
    predicate_val = getattr(index, "predicate", None)

    return CanonicalIndexSignature(
        parent_table_id=str(table_id),
        index_type=idx_type_val,
        is_unique=bool(getattr(index, "is_unique", False)),
        terms=tuple(norm_terms),
        predicate=normalize_predicate(str(predicate_val)) if predicate_val else None,
    )


def are_indexes_exactly_duplicate(idx1: Any, idx2: Any) -> tuple[bool, str]:
    """Evaluates whether two indexes on the same table are structurally identical."""
    if idx1 is idx2:
        return False, "Same index object"

    id1 = getattr(idx1, "id", None)
    id2 = getattr(idx2, "id", None)
    if id1 and id2 and id1 == id2:
        return False, "Same index object ID"

    t1 = getattr(idx1, "parent_table_id", getattr(idx1, "table_id", None))
    t2 = getattr(idx2, "parent_table_id", getattr(idx2, "table_id", None))
    if t1 and t2 and t1 != t2:
        return False, "Different parent tables"

    sig1 = compute_index_signature(idx1)
    sig2 = compute_index_signature(idx2)

    if sig1.signature_hash() == sig2.signature_hash():
        cols = ", ".join(f"'{t.term_identifier}'" for t in sig1.terms)
        return True, f"Identical {sig1.index_type.upper()} index definition on ({cols})"

    return False, "Different structural definitions"


def is_btree_leftmost_prefix(idx_narrow: Any, idx_wide: Any) -> tuple[bool, str]:
    """Evaluates if idx_narrow's terms form a strict leftmost prefix of idx_wide's terms."""
    if idx_narrow is idx_wide:
        return False, "Same index object"

    id_n = getattr(idx_narrow, "id", None)
    id_w = getattr(idx_wide, "id", None)
    if id_n and id_w and id_n == id_w:
        return False, "Same index object ID"

    t1 = getattr(idx_narrow, "parent_table_id", getattr(idx_narrow, "table_id", None))
    t2 = getattr(idx_wide, "parent_table_id", getattr(idx_wide, "table_id", None))
    if t1 and t2 and t1 != t2:
        return False, "Different parent tables"

    sig_narrow = compute_index_signature(idx_narrow)
    sig_wide = compute_index_signature(idx_wide)

    # Prefix analysis is only semantically valid for B-Tree access methods
    if sig_narrow.index_type != "btree" or sig_wide.index_type != "btree":
        return False, "Non-B-Tree index methods cannot be compared via leftmost prefix"

    if len(sig_narrow.terms) >= len(sig_wide.terms):
        return False, "Narrow index does not have strictly fewer terms than wide index"

    if len(sig_narrow.terms) == 0:
        return False, "Narrow index has no terms"

    # A wider index (unique or not) never enforces uniqueness on the narrower prefix alone
    if sig_narrow.is_unique:
        return False, "Narrow index enforces UNIQUE semantics that a wider index cannot preserve"

    # Predicates must match exactly (preserving literal case and structure)
    pred_narrow = normalize_predicate(sig_narrow.predicate)
    pred_wide = normalize_predicate(sig_wide.predicate)
    if pred_narrow != pred_wide:
        return False, "Indexes have differing partial index predicates"

    # Compare prefix terms
    for i, narrow_term in enumerate(sig_narrow.terms):
        wide_term = sig_wide.terms[i]
        if (
            narrow_term.term_identifier != wide_term.term_identifier
            or narrow_term.is_descending != wide_term.is_descending
            or narrow_term.nulls_first != wide_term.nulls_first
            or narrow_term.is_expression != wide_term.is_expression
        ):
            return False, f"Term at position {i + 1} differs between indexes"

    narrow_cols = ", ".join(f"'{t.term_identifier}'" for t in sig_narrow.terms)
    wide_cols = ", ".join(f"'{t.term_identifier}'" for t in sig_wide.terms)
    return (
        True,
        f"Index on ({narrow_cols}) is a strict leading prefix of composite index on ({wide_cols})",
    )


def is_constraint_owned_index(index: Any, table: Any) -> tuple[bool, str]:
    """Detects whether an index is engine-managed or backing a primary key / unique constraint."""
    if getattr(index, "is_primary", False):
        return True, "Primary Key backing index"

    terms = getattr(index, "terms", None)
    if terms:
        idx_cols = tuple(
            str(t.column_name).lower() for t in terms if getattr(t, "column_name", None)
        )
    else:
        cols = getattr(index, "columns", None) or getattr(index, "column_names", ())
        idx_cols = tuple(str(c).lower() for c in cols)

    # Check Primary Key match
    pk = getattr(table, "primary_key", None)
    if pk:
        pk_cols_raw = getattr(pk, "columns", None) or getattr(pk, "column_names", ())
        pk_cols = tuple(str(c).lower() for c in pk_cols_raw)
        if idx_cols and idx_cols == pk_cols:
            return True, f"Backs PRIMARY KEY '{getattr(pk, 'name', 'pk')}'"

    # Check Unique Constraints match
    for uq in getattr(table, "unique_constraints", ()):
        uq_cols_raw = getattr(uq, "columns", None) or getattr(uq, "column_names", ())
        uq_cols = tuple(str(c).lower() for c in uq_cols_raw)
        if idx_cols and idx_cols == uq_cols:
            return True, f"Backs UNIQUE constraint '{getattr(uq, 'name', 'uq')}'"

    return False, "Secondary non-constraint index"
