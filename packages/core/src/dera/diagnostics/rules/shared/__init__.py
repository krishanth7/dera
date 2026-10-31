"""Shared diagnostic signatures, engine capability matrix, and evidence helpers."""

from __future__ import annotations

from dera.diagnostics.rules.shared.capability_checks import (
    engine_automatically_indexes_foreign_keys,
    engine_enforces_check_constraints,
    engine_supports_expression_indexes,
    engine_supports_partial_indexes,
    normalize_engine_name,
)
from dera.diagnostics.rules.shared.constraint_signatures import (
    are_unique_constraints_duplicate,
    does_unique_constraint_duplicate_pk,
    validate_column_references_exist,
)
from dera.diagnostics.rules.shared.index_signatures import (
    CanonicalIndexSignature,
    CanonicalIndexTermSignature,
    are_indexes_exactly_duplicate,
    compute_index_signature,
    is_btree_leftmost_prefix,
    is_constraint_owned_index,
)

__all__ = [
    "CanonicalIndexSignature",
    "CanonicalIndexTermSignature",
    "are_indexes_exactly_duplicate",
    "are_unique_constraints_duplicate",
    "compute_index_signature",
    "does_unique_constraint_duplicate_pk",
    "engine_automatically_indexes_foreign_keys",
    "engine_enforces_check_constraints",
    "engine_supports_expression_indexes",
    "engine_supports_partial_indexes",
    "is_btree_leftmost_prefix",
    "is_constraint_owned_index",
    "normalize_engine_name",
    "validate_column_references_exist",
]
