"""DERA Migration — Phase 9.2 Dialect-Aware Type Compatibility.

Evaluates data type transitions to identify safe widenings, potential narrowings,
explicit conversion requirements, and unsupported dialect conversions.
"""

from __future__ import annotations

import re
from typing import NamedTuple

from dera.migration.enums import TypeConversionSafety


class TypeDetails(NamedTuple):
    base_name: str
    length: int | None
    precision: int | None
    scale: int | None


def parse_type_string(type_str: str) -> TypeDetails:
    """Parse native data type string into base type and numeric parameters."""
    clean = type_str.strip().lower()
    match = re.match(r"^([a-z0-9_ ]+)(?:\(([^)]+)\))?", clean)
    if not match:
        return TypeDetails(base_name=clean, length=None, precision=None, scale=None)

    base = match.group(1).strip()
    params = match.group(2)
    length: int | None = None
    precision: int | None = None
    scale: int | None = None

    if params:
        parts = [p.strip() for p in params.split(",")]
        if len(parts) == 1 and parts[0].isdigit():
            length = int(parts[0])
            precision = int(parts[0])
        elif len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            precision = int(parts[0])
            scale = int(parts[1])

    return TypeDetails(base_name=base, length=length, precision=precision, scale=scale)


# Known integer hierarchy for widening checks
INTEGER_WIDTH_RANK: dict[str, int] = {
    "smallint": 1,
    "int2": 1,
    "integer": 2,
    "int": 2,
    "int4": 2,
    "bigint": 3,
    "int8": 3,
}

TEXT_TYPES: set[str] = {"text", "varchar", "char", "character varying"}


def evaluate_type_conversion_safety(
    before_type: str,
    after_type: str,
    engine: str = "postgresql",
) -> tuple[TypeConversionSafety, str]:
    """Evaluate compatibility safety of converting before_type to after_type.

    Returns:
        (TypeConversionSafety, explanation)
    """
    b = parse_type_string(before_type)
    a = parse_type_string(after_type)

    if b.base_name == a.base_name:
        # Same base type; check lengths/precisions
        if b.length is not None and a.length is not None:
            if a.length > b.length:
                return (
                    TypeConversionSafety.SAFE_WIDENING,
                    f"Length expansion from {b.length} to {a.length} is backward-compatible for existing data.",
                )
            if a.length < b.length:
                return (
                    TypeConversionSafety.POTENTIAL_NARROWING,
                    f"Length reduction from {b.length} to {a.length} may truncate existing values longer than {a.length}.",
                )
            return (TypeConversionSafety.SAFE_WIDENING, "Equivalent type length.")

        if b.precision is not None and a.precision is not None:
            if a.precision < b.precision:
                return (
                    TypeConversionSafety.POTENTIAL_NARROWING,
                    f"Precision reduction from {b.precision} to {a.precision} may truncate significant digits.",
                )
            if (b.scale or 0) > (a.scale or 0):
                return (
                    TypeConversionSafety.POTENTIAL_NARROWING,
                    f"Scale reduction from {b.scale} to {a.scale} may truncate decimal fractions.",
                )
            return (
                TypeConversionSafety.SAFE_WIDENING,
                "Precision/scale expansion is backward-compatible.",
            )

        return (TypeConversionSafety.SAFE_WIDENING, "Equivalent native data types.")

    # Integer hierarchy widening
    if b.base_name in INTEGER_WIDTH_RANK and a.base_name in INTEGER_WIDTH_RANK:
        b_rank = INTEGER_WIDTH_RANK[b.base_name]
        a_rank = INTEGER_WIDTH_RANK[a.base_name]
        if a_rank > b_rank:
            return (
                TypeConversionSafety.SAFE_WIDENING,
                f"Integer widening from '{b.base_name}' to '{a.base_name}' preserves all existing values.",
            )
        if a_rank < b_rank:
            return (
                TypeConversionSafety.POTENTIAL_NARROWING,
                f"Integer narrowing from '{b.base_name}' to '{a.base_name}' risks overflow on values exceeding destination bounds.",
            )

    # Varchar to Text (Widening)
    if b.base_name in ("varchar", "char", "character varying") and a.base_name == "text":
        return (
            TypeConversionSafety.SAFE_WIDENING,
            f"Converting '{b.base_name}' to unbounded 'text' is safe for all existing strings.",
        )

    # Text to Varchar (Narrowing)
    if b.base_name == "text" and a.base_name in ("varchar", "character varying"):
        limit_desc = f" ({a.length})" if a.length else ""
        return (
            TypeConversionSafety.POTENTIAL_NARROWING,
            f"Converting unbounded 'text' to restricted '{a.base_name}{limit_desc}' may truncate existing long strings.",
        )

    # Date to Timestamp (Widening)
    if b.base_name == "date" and "timestamp" in a.base_name:
        return (
            TypeConversionSafety.SAFE_WIDENING,
            "Date to timestamp conversion adds time component without loss of date information.",
        )

    # Timestamp to Date (Narrowing)
    if "timestamp" in b.base_name and a.base_name == "date":
        return (
            TypeConversionSafety.POTENTIAL_NARROWING,
            "Timestamp to date conversion discards time of day fractions.",
        )

    # Cross-category requires explicit casting / review
    return (
        TypeConversionSafety.EXPLICIT_CONVERSION_REQUIRED,
        f"Altering column from '{before_type}' to '{after_type}' requires explicit type casting and data validation.",
    )
