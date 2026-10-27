"""DERA Canonical Metadata Normalization & Identity — Stable Object Identity.

Implements collision-resistant, cryptographic, deterministic object identifiers (ObjectId)
derived from canonical schema hierarchy and length-prefixed SHA-256 component hashing.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

from dera.metadata.enums import ObjectKind


def compute_stable_object_id(
    engine: str,
    object_kind: ObjectKind,
    native_name: str,
    namespace: str | None = None,
    parent_id: str | None = None,
    workspace_id: str | None = None,
    connection_id: str | None = None,
    terms: Sequence[str] | None = None,
) -> str:
    """Generate a deterministic, collision-resistant canonical ObjectId.

    Formulation:
    Uses length-prefixed canonical serialization of all hierarchy tokens to prevent
    delimiter collision attacks (e.g. 'a' + 'bc' colliding with 'ab' + 'c'):

      FRAME = "v1"
              + "|" + len(engine) + ":" + engine
              + "|" + len(workspace_id or "") + ":" + (workspace_id or "")
              + "|" + len(connection_id or "") + ":" + (connection_id or "")
              + "|" + len(namespace or "") + ":" + (namespace or "")
              + "|" + len(object_kind.value) + ":" + object_kind.value
              + "|" + len(parent_id or "") + ":" + (parent_id or "")
              + "|" + len(native_name) + ":" + native_name

    For constraints, indexes, or composite elements with term sequences:
      + "|" + count(terms) + "[" + sum(len(t) + ":" + t) + "]"

    The SHA-256 digest of this canonical frame is computed, and the first 24
    hexadecimal characters are formatted as:
      `dera:<object_kind>:<24_hex_chars>`

    Properties:
    1. Deterministic across inspection executions on identical schemas.
    2. Zero random numbers or non-reproducible state.
    3. Isolated across workspaces and database engines.
    4. Free of plain credentials, connection strings, or system paths.
    """
    clean_engine = engine.strip().lower()
    clean_ws = (workspace_id or "").strip()
    clean_conn = (connection_id or "").strip()
    clean_ns = (namespace or "").strip()
    clean_parent = (parent_id or "").strip()
    clean_name = native_name.strip()

    components: list[str] = [
        "v1",
        f"{len(clean_engine)}:{clean_engine}",
        f"{len(clean_ws)}:{clean_ws}",
        f"{len(clean_conn)}:{clean_conn}",
        f"{len(clean_ns)}:{clean_ns}",
        f"{len(object_kind.value)}:{object_kind.value}",
        f"{len(clean_parent)}:{clean_parent}",
        f"{len(clean_name)}:{clean_name}",
    ]

    if terms:
        serialized_terms = ",".join(f"{len(t)}:{t}" for t in terms)
        components.append(f"terms:{len(terms)}[{serialized_terms}]")

    frame = "|".join(components).encode("utf-8")
    digest = hashlib.sha256(frame).hexdigest()[:24]

    return f"dera:{object_kind.value}:{digest}"


def generate_unnamed_constraint_name(
    table_name: str,
    constraint_kind: str,
    columns: Sequence[str],
) -> str:
    """Generate a stable deterministic surrogate name for unnamed constraints.

    Some engines (such as SQLite or MySQL) do not assign explicit catalog names
    to certain CHECK or inline UNIQUE constraints. This helper creates a deterministic
    descriptor like `chk_orders_amount` or `unq_users_email` without falsely presenting
    it as a native database catalog identifier.
    """
    kind = constraint_kind.strip().lower()
    if "check" in kind or "chk" in kind:
        prefix = "chk"
    elif "unique" in kind or "unq" in kind:
        prefix = "unq"
    elif "foreign" in kind or "fk" in kind:
        prefix = "fk"
    else:
        prefix = kind[:3]

    col_str = "_".join(c.strip().lower() for c in sorted(columns))
    return f"_{prefix}_{table_name.strip().lower()}_{col_str}"
