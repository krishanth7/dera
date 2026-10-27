"""DERA API — Identifier Validation Contracts.

Provides reusable validators and regex constraints for path parameters,
slugs, UUIDs, and database schema object names.
"""

import re

SLUG_REGEX = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
UUID_REGEX = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
DB_IDENTIFIER_REGEX = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,62}$")
QUALIFIED_IDENTIFIER_REGEX = re.compile(
    r"^[a-zA-Z_][a-zA-Z0-9_]{0,62}(?:\.[a-zA-Z_][a-zA-Z0-9_]{0,62})?$"
)


def validate_slug(slug: str) -> str:
    """Validates URL-safe lowercase slug parameter."""
    if not (1 <= len(slug) <= 64):
        raise ValueError(f"Slug length must be between 1 and 64 characters, got {len(slug)}")
    if not SLUG_REGEX.match(slug):
        raise ValueError(
            f"Invalid slug format: '{slug}'. Must be kebab-case lowercase alphanumeric."
        )
    return slug


def validate_uuid_str(uuid_str: str) -> str:
    """Validates standard RFC 4122 UUID string format."""
    if not UUID_REGEX.match(uuid_str):
        raise ValueError(f"Invalid UUID string format: '{uuid_str}'")
    return uuid_str.lower()


def validate_db_identifier(name: str) -> str:
    """Validates safe database object name (table, column, view) under standard 63-byte limits."""
    if not (1 <= len(name) <= 63):
        raise ValueError(f"Identifier length must be between 1 and 63 characters, got {len(name)}")
    if not DB_IDENTIFIER_REGEX.match(name):
        raise ValueError(
            f"Invalid database identifier: '{name}'. Must start with letter/underscore and contain only alphanumeric, $, or _."
        )
    return name


def validate_qualified_identifier(name: str) -> tuple[str | None, str]:
    """Validates optional schema-qualified database object name (e.g. 'public.users').

    Returns a tuple of (schema, table). If unqualified, schema is None.
    """
    if not (1 <= len(name) <= 128):
        raise ValueError(
            f"Qualified identifier length must be between 1 and 128 characters, got {len(name)}"
        )
    if not QUALIFIED_IDENTIFIER_REGEX.match(name):
        raise ValueError(
            f"Invalid qualified database identifier: '{name}'. Must be 'name' or 'schema.name'."
        )
    parts = name.split(".")
    if len(parts) == 1:
        return (None, validate_db_identifier(parts[0]))
    elif len(parts) == 2:
        return (validate_db_identifier(parts[0]), validate_db_identifier(parts[1]))
    raise ValueError(f"Too many qualifier parts in '{name}'. Maximum 2 parts allowed.")
