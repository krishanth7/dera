"""DERA Diagnostics — Identifier Naming Conventions & Reserved Words.

Defines deterministic regex profiles for database identifier conventions
(snake_case, camelCase, PascalCase, kebab-case) and verified engine-specific
SQL reserved word dictionaries.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from enum import StrEnum

from dera.diagnostics.metrics.models import NamingComplianceMetrics


class NamingProfile(StrEnum):
    """Supported identifier naming convention profiles."""

    SNAKE_CASE = "snake_case"
    CAMEL_CASE = "camelCase"
    PASCAL_CASE = "PascalCase"
    KEBAB_CASE = "kebab-case"
    UPPER_SNAKE_CASE = "UPPER_SNAKE_CASE"


# Deterministic regular expression patterns for naming convention profiles
_NAMING_PATTERNS: dict[str, re.Pattern[str]] = {
    NamingProfile.SNAKE_CASE: re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$"),
    NamingProfile.CAMEL_CASE: re.compile(r"^[a-z][a-zA-Z0-9]*$"),
    NamingProfile.PASCAL_CASE: re.compile(r"^[A-Z][a-zA-Z0-9]*$"),
    NamingProfile.KEBAB_CASE: re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$"),
    NamingProfile.UPPER_SNAKE_CASE: re.compile(r"^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$"),
}

# Engine-specific SQL reserved keywords
_COMMON_SQL_RESERVED: frozenset[str] = frozenset(
    {
        "select",
        "insert",
        "update",
        "delete",
        "from",
        "where",
        "and",
        "or",
        "not",
        "in",
        "is",
        "null",
        "like",
        "order",
        "group",
        "by",
        "having",
        "join",
        "inner",
        "left",
        "right",
        "outer",
        "full",
        "on",
        "as",
        "distinct",
        "table",
        "view",
        "index",
        "create",
        "alter",
        "drop",
        "truncate",
        "schema",
        "database",
        "primary",
        "foreign",
        "key",
        "references",
        "check",
        "unique",
        "constraint",
        "default",
        "values",
        "into",
        "set",
        "union",
        "all",
        "case",
        "when",
        "then",
        "else",
        "end",
        "cast",
        "between",
        "exists",
        "user",
        "limit",
        "offset",
        "desc",
        "asc",
        "with",
        "column",
        "rows",
        "range",
    }
)

_POSTGRES_RESERVED: frozenset[str] = _COMMON_SQL_RESERVED.union(
    {
        "analyse",
        "analyze",
        "authorization",
        "binary",
        "concurrently",
        "cross",
        "current_catalog",
        "current_date",
        "current_role",
        "current_schema",
        "current_time",
        "current_timestamp",
        "current_user",
        "do",
        "freeze",
        "grant",
        "ilike",
        "initially",
        "lateral",
        "leading",
        "localtime",
        "localtimestamp",
        "natural",
        "nulls",
        "only",
        "placing",
        "returning",
        "session_user",
        "similar",
        "tablefunc",
        "trailing",
        "variadic",
        "verbose",
        "window",
    }
)

_MYSQL_RESERVED: frozenset[str] = _COMMON_SQL_RESERVED.union(
    {
        "accessible",
        "add",
        "all",
        "alter",
        "analyze",
        "asensitive",
        "before",
        "bigint",
        "binary",
        "blob",
        "both",
        "call",
        "cascade",
        "change",
        "char",
        "character",
        "collate",
        "condition",
        "continue",
        "convert",
        "cursor",
        "database",
        "databases",
        "day_hour",
        "day_microsecond",
        "day_minute",
        "day_second",
        "dec",
        "decimal",
        "declare",
        "delayed",
        "describe",
        "deterministic",
        "distinctrow",
        "div",
        "double",
        "dual",
        "each",
        "elseif",
        "enclosed",
        "escaped",
        "explain",
        "float",
        "float4",
        "float8",
        "force",
        "fulltext",
        "high_priority",
        "hour_microsecond",
        "hour_minute",
        "hour_second",
        "ignore",
        "index",
        "infile",
        "inout",
        "insensitive",
        "int",
        "int1",
        "int2",
        "int3",
        "int4",
        "int8",
        "integer",
        "interval",
        "iterate",
        "keys",
        "kill",
        "linear",
        "lines",
        "load",
        "lock",
        "long",
        "longblob",
        "longtext",
        "loop",
        "low_priority",
        "master_ssl_verify_server_cert",
        "match",
        "maxvalue",
        "mediumblob",
        "mediumint",
        "mediumtext",
        "middleint",
        "minute_microsecond",
        "minute_second",
        "mod",
        "modifies",
        "no_write_to_binlog",
        "numeric",
        "optimize",
        "optimizer_costs",
        "option",
        "optionally",
        "out",
        "outfile",
        "partition",
        "precision",
        "procedure",
        "purge",
        "read",
        "reads",
        "real",
        "recursive",
        "release",
        "rename",
        "repeat",
        "replace",
        "require",
        "resignal",
        "restrict",
        "return",
        "revoke",
        "rlike",
        "schema",
        "schemas",
        "second_microsecond",
        "sensitive",
        "separator",
        "show",
        "signal",
        "smallint",
        "spatial",
        "specific",
        "sql",
        "sqlexception",
        "sqlstate",
        "sqlwarning",
        "sql_big_result",
        "sql_calc_found_rows",
        "sql_small_result",
        "ssl",
        "starting",
        "stored",
        "straight_join",
        "terminated",
        "tinyblob",
        "tinyint",
        "tinytext",
        "to",
        "trailing",
        "trigger",
        "undo",
        "unlock",
        "unsigned",
        "use",
        "using",
        "utc_date",
        "utc_time",
        "utc_timestamp",
        "varbinary",
        "varchar",
        "varcharacter",
        "varying",
        "virtual",
        "while",
        "write",
        "xor",
        "year_month",
        "zerofill",
    }
)

_SQLITE_RESERVED: frozenset[str] = _COMMON_SQL_RESERVED.union(
    {
        "abort",
        "action",
        "add",
        "after",
        "all",
        "alter",
        "always",
        "analyze",
        "attach",
        "autoincrement",
        "before",
        "begin",
        "cascade",
        "conflict",
        "cross",
        "current",
        "current_date",
        "current_time",
        "current_timestamp",
        "database",
        "deferrable",
        "deferred",
        "detach",
        "each",
        "exclusive",
        "explain",
        "fail",
        "filter",
        "first",
        "following",
        "for",
        "foreign",
        "generated",
        "glob",
        "groups",
        "if",
        "ignore",
        "immediate",
        "indexed",
        "initially",
        "instead",
        "intersect",
        "isnull",
        "key",
        "last",
        "match",
        "materialized",
        "natural",
        "no",
        "notnull",
        "nothing",
        "nulls",
        "others",
        "over",
        "partition",
        "plan",
        "pragma",
        "query",
        "raise",
        "recursive",
        "regexp",
        "reindex",
        "release",
        "rename",
        "replace",
        "restrict",
        "rollback",
        "row",
        "savepoint",
        "stored",
        "strict",
        "temp",
        "temporary",
        "ties",
        "transaction",
        "trigger",
        "unbounded",
        "vacuum",
        "view",
        "virtual",
        "window",
        "without",
    }
)


def matches_naming_profile(identifier: str, profile_name: str = NamingProfile.SNAKE_CASE) -> bool:
    """Verifies whether an identifier strictly satisfies the specified naming profile."""
    # Strip optional surrounding quotes (e.g. "users" or `users`)
    cleaned = identifier.strip().strip('"').strip("`").strip("[]")
    if not cleaned:
        return False

    pattern = _NAMING_PATTERNS.get(profile_name)
    if pattern is None:
        # Fallback to snake_case if custom profile is unconfigured
        pattern = _NAMING_PATTERNS[NamingProfile.SNAKE_CASE]

    return bool(pattern.match(cleaned))


def is_reserved_word(identifier: str, engine: str = "generic") -> bool:
    """Checks whether an identifier conflicts with engine-specific SQL reserved keywords."""
    cleaned = identifier.strip().strip('"').strip("`").strip("[]").lower()
    if not cleaned:
        return False

    eng = engine.strip().lower()
    if "postgres" in eng or "supabase" in eng:
        return cleaned in _POSTGRES_RESERVED
    elif "mysql" in eng or "maria" in eng:
        return cleaned in _MYSQL_RESERVED
    elif "sqlite" in eng:
        return cleaned in _SQLITE_RESERVED

    return cleaned in _COMMON_SQL_RESERVED


def compute_naming_compliance(
    identifiers: Sequence[str],
    profile_name: str = NamingProfile.SNAKE_CASE,
) -> NamingComplianceMetrics:
    """Computes aggregate naming convention compliance across a list of identifiers."""
    id_list = list(identifiers)
    total = len(id_list)
    if total == 0:
        return NamingComplianceMetrics(
            profile_name=profile_name,
            total_evaluated=0,
            compliant_count=0,
            non_compliant_count=0,
            compliance_ratio=1.0,
        )

    compliant = sum(1 for ident in id_list if matches_naming_profile(ident, profile_name))
    non_compliant = total - compliant
    ratio = round(compliant / total, 4)

    return NamingComplianceMetrics(
        profile_name=profile_name,
        total_evaluated=total,
        compliant_count=compliant,
        non_compliant_count=non_compliant,
        compliance_ratio=ratio,
    )
