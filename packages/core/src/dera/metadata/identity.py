"""DERA Canonical Metadata Normalization & Identity — Stable Object Identity.

Implements collision-resistant, cryptographic, deterministic object identifiers (ObjectId)
derived from canonical schema hierarchy and length-prefixed SHA-256 component hashing.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

from dera.metadata.enums import ObjectKind

type ObjectId = str


def compute_stable_object_id(
    engine: str = "postgresql",
    object_kind: ObjectKind | str = ObjectKind.TABLE,
    native_name: str | tuple[str, ...] = "",
    namespace: str | None = None,
    parent_id: str | None = None,
    workspace_id: str | None = None,
    connection_id: str | None = None,
    terms: Sequence[str] | None = None,
    *,
    kind: ObjectKind | str | None = None,
    components: Sequence[str] | None = None,
) -> str:
    """Generate a deterministic, collision-resistant canonical ObjectId."""
    if kind is not None:
        object_kind = kind
    if components is not None:
        if len(components) == 1:
            native_name = components[0]
        elif len(components) == 2:
            parent_id, native_name = str(components[0]), str(components[1])
        elif len(components) >= 3:
            parent_id, native_name = str(components[-2]), str(components[-1])
    if isinstance(native_name, (tuple, list)):
        if len(native_name) == 1:
            native_name = native_name[0]
        elif len(native_name) == 2:
            parent_id, native_name = str(native_name[0]), str(native_name[1])
        elif len(native_name) >= 3:
            parent_id, native_name = str(native_name[-2]), str(native_name[-1])
    known_engines = ("postgresql", "postgres", "sqlite", "mysql", "mariadb", "supabase")
    if isinstance(engine, ObjectKind) or (
        isinstance(engine, str)
        and engine.lower() not in known_engines
        and str(object_kind).lower() in known_engines
    ):
        engine, object_kind = object_kind, engine

    if isinstance(object_kind, str):
        try:
            object_kind = ObjectKind(object_kind)
        except ValueError:
            pass
    kind_val = object_kind.value if hasattr(object_kind, "value") else str(object_kind)

    clean_engine = str(engine).strip().lower()
    clean_ws = (workspace_id or "").strip()
    clean_conn = (connection_id or "").strip()
    clean_ns = (namespace or "").strip()
    clean_parent = (parent_id or "").strip()
    clean_name = str(native_name).strip()

    components: list[str] = [
        "v1",
        f"{len(clean_engine)}:{clean_engine}",
        f"{len(clean_ws)}:{clean_ws}",
        f"{len(clean_conn)}:{clean_conn}",
        f"{len(clean_ns)}:{clean_ns}",
        f"{len(kind_val)}:{kind_val}",
        f"{len(clean_parent)}:{clean_parent}",
        f"{len(clean_name)}:{clean_name}",
    ]

    if terms:
        serialized_terms = ",".join(f"{len(t)}:{t}" for t in terms)
        components.append(f"terms:{len(terms)}[{serialized_terms}]")

    frame = "|".join(components).encode("utf-8")
    digest = hashlib.sha256(frame).hexdigest()[:24]

    return f"dera:{kind_val}:{digest}"


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
