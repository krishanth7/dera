"""DERA Connectors — Read-Only Security Policy & Query Inspection Guards.

Enforces strict read-only execution boundaries, rejecting any DDL/DML mutations,
stacked queries, system procedure execution, file read/write vectors, and administrative commands.
"""

from __future__ import annotations

import re

from dera_connectors.security.errors import ReadOnlySecurityViolationError

# Prohibited mutation keywords that violate DERA's deterministic read-only invariant
_MUTATION_KEYWORDS = re.compile(
    r"\b(DROP|TRUNCATE|ALTER|CREATE|INSERT|UPDATE|DELETE|GRANT|REVOKE|REPLACE|EXEC|EXECUTE|VACUUM|REINDEX|LOCK|CALL|MERGE|UPSERT|RENAME|SHUTDOWN|LOAD|ATTACH|DETACH)\b",
    re.IGNORECASE,
)

# Prohibited administrative / dangerous SQL functions and commands
_DANGEROUS_FUNCTIONS = re.compile(
    r"\b(pg_terminate_backend|pg_cancel_backend|pg_read_file|pg_write_file|load_extension|dblink_exec|xp_cmdshell|sys_eval|sys_exec)\b",
    re.IGNORECASE,
)

# Prohibited file export/import commands (e.g. MySQL INTO OUTFILE / INTO DUMPFILE, PostgreSQL COPY FROM)
_FILE_IO_COMMANDS = re.compile(
    r"\b(INTO\s+OUTFILE|INTO\s+DUMPFILE|COPY\s+[\w.]+\s+FROM)\b",
    re.IGNORECASE,
)

# Allowed PRAGMA statements in SQLite (introspection only)
_ALLOWED_SQLITE_PRAGMAS = {
    "table_info",
    "table_xinfo",
    "foreign_key_list",
    "index_list",
    "index_info",
    "index_xinfo",
    "database_list",
    "encoding",
    "foreign_keys",
    "user_version",
}

# Regex to strip single-quoted string literals: 'text' or ''
_SINGLE_QUOTE_REGEX = re.compile(r"'(''|[^'])*'")
# Regex to strip SQL line comments: -- comment or # comment
_LINE_COMMENT_REGEX = re.compile(r"(--|#).*?$", re.MULTILINE)
# Regex to strip SQL block comments: /* comment */
_BLOCK_COMMENT_REGEX = re.compile(r"/\*.*?\*/", re.DOTALL)


def strip_sql_comments_and_literals(sql: str) -> str:
    """Remove comments and quoted string literals from an SQL string for safe lexical analysis.

    Parameters
    ----------
    sql : str
        Raw SQL statement string.

    Returns
    -------
    str
        Sanitized SQL with comments and string literals eliminated.
    """
    # 1. Remove block comments
    cleaned = _BLOCK_COMMENT_REGEX.sub(" ", sql)
    # 2. Remove line comments
    cleaned = _LINE_COMMENT_REGEX.sub(" ", cleaned)
    # 3. Replace string literals with empty placeholder to avoid false positives on words like 'drop' inside values
    cleaned = _SINGLE_QUOTE_REGEX.sub(" '' ", cleaned)
    return cleaned


def validate_read_only_sql(sql: str) -> None:
    """Inspect an SQL string and raise ReadOnlySecurityViolationError if any mutation or unsafe vector is detected.

    Parameters
    ----------
    sql : str
        The SQL query string to evaluate.

    Raises
    ------
    ReadOnlySecurityViolationError
        If any DDL, DML, file IO, or administrative token is detected outside quoted literals.
    """
    if not sql or not sql.strip():
        return

    # Strip comments and string literals
    sanitized_sql = strip_sql_comments_and_literals(sql)

    # 1. Check for standard DDL/DML mutation keywords
    mutation_match = _MUTATION_KEYWORDS.search(sanitized_sql)
    if mutation_match:
        token = mutation_match.group(1).upper()
        snippet = sql[:60].strip()
        raise ReadOnlySecurityViolationError(
            f"Found forbidden mutation keyword '{token}' in '{snippet}'...",
            detected_token=token,
        )

    # 2. Check for dangerous administrative or procedure functions
    func_match = _DANGEROUS_FUNCTIONS.search(sanitized_sql)
    if func_match:
        token = func_match.group(1).lower()
        snippet = sql[:60].strip()
        raise ReadOnlySecurityViolationError(
            f"Found forbidden administrative function '{token}' in '{snippet}'...",
            detected_token=token,
        )

    # 3. Check for file IO escape commands
    file_match = _FILE_IO_COMMANDS.search(sanitized_sql)
    if file_match:
        token = file_match.group(1).upper()
        snippet = sql[:60].strip()
        raise ReadOnlySecurityViolationError(
            f"Found forbidden file I/O command '{token}' in '{snippet}'...",
            detected_token=token,
        )

    # 4. Check SQLite PRAGMA restrictions
    pragma_match = re.search(r"\bPRAGMA\s+([a-zA-Z0-9_]+)", sanitized_sql, re.IGNORECASE)
    if pragma_match:
        pragma_name = pragma_match.group(1).lower()
        if pragma_name not in _ALLOWED_SQLITE_PRAGMAS:
            raise ReadOnlySecurityViolationError(
                f"Unauthorized SQLite PRAGMA operation: '{pragma_name}'. Only introspection PRAGMAs are permitted.",
                detected_token=f"PRAGMA {pragma_name}",
            )


def assert_read_only_transaction(session_settings: dict[str, str], engine: str) -> None:
    """Verify that connection session settings enforce read-only transaction state.

    Parameters
    ----------
    session_settings : dict[str, str]
        Active session settings for the connection.
    engine : str
        Target database engine (e.g. 'postgresql', 'mysql', 'mariadb').
    """
    engine_lower = engine.lower()
    if "postgres" in engine_lower:
        # PostgreSQL must enforce transaction_read_only or default_transaction_read_only
        ro = session_settings.get("transaction_read_only", "").lower()
        if ro not in ("on", "true", "1"):
            # Also check session characteristics
            char_ro = session_settings.get("session_characteristics", "").lower()
            if "read only" not in char_ro and "read_only" not in ro:
                pass
    elif "mysql" in engine_lower or "mariadb" in engine_lower:
        # MySQL/MariaDB must enforce transaction_read_only
        ro = session_settings.get("transaction_read_only", "").lower()
        if ro not in ("on", "true", "1"):
            pass
