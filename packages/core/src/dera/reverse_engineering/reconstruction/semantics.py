"""Engine-specific semantics handler for Phase 6.2 Structural Reconstruction.

Provides deterministic interpretation of dialect-specific identity columns,
sequence-backed defaults, type affinities, generated columns, and constraint behaviors
across PostgreSQL (and Supabase), SQLite, MySQL, and MariaDB.
"""

from typing import Any

from dera.metadata.enums import GenerationMode
from dera.metadata.models import CanonicalColumn, CanonicalTable
from dera.reverse_engineering.reconstruction.models import (
    DefaultKind,
    DefaultValueMetadata,
    GeneratedColumnMetadata,
    IdentityMetadata,
)


def normalize_engine_name(engine: str) -> str:
    """Normalize database engine identifier to its canonical dialect family."""
    normalized = engine.strip().lower()
    if normalized in ("supabase", "postgres", "postgresql"):
        return "postgresql"
    if normalized in ("sqlite", "sqlite3"):
        return "sqlite"
    if normalized in ("mysql", "aurora-mysql"):
        return "mysql"
    if normalized == "mariadb":
        return "mariadb"
    return normalized


def classify_default_value(raw_default: str | None, engine: str) -> DefaultValueMetadata:
    """Classify a column default expression into literal, expression, sequence, or none.

    Preserves the raw expression as inert text. Never executes code.
    """
    if raw_default is None or raw_default.strip() == "":
        return DefaultValueMetadata(kind=DefaultKind.NO_DEFAULT, raw_expression=None)

    trimmed = raw_default.strip()
    upper = trimmed.upper()

    # PostgreSQL sequence-backed defaults
    if upper.startswith("NEXTVAL(") or "NEXTVAL(" in upper:
        return DefaultValueMetadata(kind=DefaultKind.EXPRESSION, raw_expression=trimmed)

    # Standard SQL and dialect expression defaults
    expression_keywords = (
        "CURRENT_TIMESTAMP",
        "CURRENT_DATE",
        "CURRENT_TIME",
        "NOW()",
        "GEN_RANDOM_UUID()",
        "UUID_GENERATE_V4()",
        "UUID()",
        "UUID_TO_BIN(",
        "STRFTIME(",
        "RANDOM()",
        "RAND()",
    )
    if any(kw in upper for kw in expression_keywords) or (
        trimmed.startswith("(") and trimmed.endswith(")")
    ):
        return DefaultValueMetadata(kind=DefaultKind.EXPRESSION, raw_expression=trimmed)

    # Dialect literal formats (quoted string, numbers, NULL, booleans)
    if (
        (trimmed.startswith("'") and trimmed.endswith("'"))
        or (trimmed.startswith('"') and trimmed.endswith('"'))
        or upper in ("NULL", "TRUE", "FALSE")
        or trimmed.lstrip("-").replace(".", "", 1).isdigit()
    ):
        return DefaultValueMetadata(kind=DefaultKind.LITERAL, raw_expression=trimmed)

    # PostgreSQL type-casted literals: 'active'::character varying
    if "::" in trimmed:
        prefix = trimmed.split("::", 1)[0].strip()
        if (prefix.startswith("'") and prefix.endswith("'")) or prefix.isdigit():
            return DefaultValueMetadata(kind=DefaultKind.LITERAL, raw_expression=trimmed)
        return DefaultValueMetadata(kind=DefaultKind.EXPRESSION, raw_expression=trimmed)

    return DefaultValueMetadata(kind=DefaultKind.LITERAL, raw_expression=trimmed)


def extract_identity_metadata(column: CanonicalColumn, engine: str) -> IdentityMetadata:
    """Extract dialect-specific identity and auto-increment properties."""
    dialect = normalize_engine_name(engine)
    extra = getattr(column, "extra_metadata", None) or {}
    raw_default = (
        getattr(column, "default_expression", None) or getattr(column, "default_value", None) or ""
    ).strip()
    upper_default = raw_default.upper()

    # Explicit identity attributes in column or extra_metadata
    if getattr(column, "is_identity", False) or extra.get("is_identity") is True:
        strategy = extra.get("identity_generation", "ALWAYS")
        seq_name = extra.get("sequence_name")
        return IdentityMetadata(
            is_identity=True,
            is_auto_increment=False,
            strategy=strategy,
            sequence_name=seq_name,
        )

    # MySQL / MariaDB AUTO_INCREMENT
    if dialect in ("mysql", "mariadb"):
        is_auto = (
            extra.get("is_auto_increment", False)
            or "AUTO_INCREMENT" in extra.get("extra", "").upper()
            or "AUTO_INCREMENT" in str(getattr(column, "native_data_type", "")).upper()
        )
        if is_auto:
            return IdentityMetadata(
                is_identity=False,
                is_auto_increment=True,
                strategy="AUTO_INCREMENT",
            )

    # PostgreSQL SERIAL / sequence defaults
    if dialect == "postgresql":
        if "NEXTVAL(" in upper_default:
            # Extract sequence name if possible: nextval('users_id_seq'::regclass)
            seq_name = None
            if "'" in raw_default:
                parts = raw_default.split("'", 2)
                if len(parts) >= 2:
                    seq_name = parts[1]
            return IdentityMetadata(
                is_identity=False,
                is_auto_increment=True,
                strategy="SEQUENCE",
                sequence_name=seq_name,
            )

    # SQLite rowid aliasing
    if dialect == "sqlite":
        # SQLite INTEGER PRIMARY KEY acts as an alias to rowid
        is_rowid_alias = extra.get("is_rowid_alias", False)
        if is_rowid_alias:
            return IdentityMetadata(
                is_identity=False,
                is_auto_increment=True,
                strategy="ROWID",
            )

    return IdentityMetadata(is_identity=False, is_auto_increment=False)


def extract_generated_metadata(column: CanonicalColumn) -> GeneratedColumnMetadata:
    """Extract generated/computed column metadata."""
    extra = getattr(column, "extra_metadata", None) or {}
    is_gen = getattr(column, "is_generated", False) or extra.get("is_generated", False)
    gen_expr = getattr(column, "generation_expression", None) or extra.get("generation_expression")

    if not is_gen and not gen_expr:
        return GeneratedColumnMetadata(is_generated=False)

    gen_mode = getattr(column, "generation_mode", None)
    if gen_mode is None or gen_mode == GenerationMode.NONE:
        mode_str = extra.get("generation_mode", "").upper()
        if mode_str in ("STORED", "PERSISTENT"):
            gen_mode = GenerationMode.STORED
        elif mode_str in ("VIRTUAL",):
            gen_mode = GenerationMode.VIRTUAL

    is_stored = gen_mode == GenerationMode.STORED or extra.get("is_stored", False)

    return GeneratedColumnMetadata(
        is_generated=True,
        generation_mode=gen_mode if gen_mode != GenerationMode.NONE else None,
        expression=gen_expr,
        is_stored=is_stored,
    )


def extract_table_native_attributes(table: CanonicalTable, engine: str) -> dict[str, Any]:
    """Extract engine-specific attributes for a table (e.g. WITHOUT ROWID, STRICT, storage engine)."""
    dialect = normalize_engine_name(engine)
    attrs: dict[str, Any] = {}
    extra = getattr(table, "extra_metadata", None) or {}

    if dialect == "sqlite":
        if "without_rowid" in extra:
            attrs["without_rowid"] = extra["without_rowid"]
        if "is_strict" in extra:
            attrs["is_strict"] = extra["is_strict"]

    elif dialect in ("mysql", "mariadb"):
        for key in ("engine", "row_format", "collation", "comment", "auto_increment"):
            if key in extra:
                attrs[key] = extra[key]

    elif dialect == "postgresql":
        for key in ("tablespace", "persistence", "partition_by", "has_oids"):
            if key in extra:
                attrs[key] = extra[key]

    # Preserve any remaining custom extra attributes
    for k, v in extra.items():
        if k not in attrs:
            attrs[k] = v

    return attrs
