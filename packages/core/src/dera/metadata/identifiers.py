"""DERA Canonical Metadata Normalization & Identity — Identifier Handling.

Provides deterministic identifier normalization, case-folding analysis,
unquoting utilities, and qualified name generation across SQL dialects.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Identifier:
    """Represents a database identifier with engine-specific quoting and case semantics."""

    raw_name: str
    engine: str
    is_quoted: bool = False
    quote_char: str | None = None

    @classmethod
    def parse(cls, raw: str, engine: str) -> Identifier:
        """Parse raw identifier token and determine quoting and raw contents.

        Handles standard quotes:
        - ANSI double quotes: "my_table"
        - MySQL backticks: `my_table`
        - SQL Server brackets: [my_table]
        """
        trimmed = raw.strip()
        if not trimmed:
            return cls(raw_name="", engine=engine, is_quoted=False, quote_char=None)

        # Double quotes
        if trimmed.startswith('"') and trimmed.endswith('"') and len(trimmed) >= 2:
            return cls(
                raw_name=trimmed[1:-1].replace('""', '"'),
                engine=engine,
                is_quoted=True,
                quote_char='"',
            )

        # Backticks
        if trimmed.startswith("`") and trimmed.endswith("`") and len(trimmed) >= 2:
            return cls(
                raw_name=trimmed[1:-1].replace("``", "`"),
                engine=engine,
                is_quoted=True,
                quote_char="`",
            )

        # Brackets
        if trimmed.startswith("[") and trimmed.endswith("]") and len(trimmed) >= 2:
            return cls(
                raw_name=trimmed[1:-1].replace("]]", "]"),
                engine=engine,
                is_quoted=True,
                quote_char="[",
            )

        return cls(raw_name=trimmed, engine=engine, is_quoted=False, quote_char=None)

    @property
    def canonical_name(self) -> str:
        """Returns the identifier string for canonical catalog storage.

        DERA strictly preserves the exact declared casing of identifiers
        rather than indiscriminately lowercasing, while recording case-sensitivity
        flags so that equivalence checks respect engine rules.
        """
        return self.raw_name

    def lookup_key(self) -> str:
        """Returns case-folded lookup token according to engine dialect rules.

        - PostgreSQL: unquoted identifiers fold to lower case; quoted preserve case.
        - SQLite: ASCII characters fold to lower case for case-insensitive matching.
        - MySQL / MariaDB: standard lookup uses lower case for case-insensitive collation.
        """
        eng = self.engine.lower()
        if eng in ("postgresql", "postgres", "supabase"):
            return self.raw_name if self.is_quoted else self.raw_name.lower()
        if eng == "sqlite":
            return self.raw_name.lower()
        if eng in ("mysql", "mariadb"):
            return self.raw_name.lower()

        return self.raw_name


def qualify_identifier(namespace: str | None, name: str) -> str:
    """Format fully qualified identifier: [namespace.]name."""
    if namespace:
        return f"{namespace}.{name}"
    return name
