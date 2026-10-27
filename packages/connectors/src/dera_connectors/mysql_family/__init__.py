"""DERA MySQL-Family Shared Connector Subsystem.

Shared utilities, security policies, catalog introspection routines, type handlers,
and error mappers for MySQL and MariaDB adapters.
"""

from __future__ import annotations

from dera_connectors.mysql_family.catalog import (
    introspect_check_constraints,
    introspect_columns,
    introspect_foreign_keys,
    introspect_identity,
    introspect_indexes,
    introspect_primary_key,
    introspect_schemas,
    introspect_tables,
    introspect_triggers,
    introspect_unique_constraints,
    introspect_views,
)
from dera_connectors.mysql_family.connection import MySqlFamilyConnectionManager
from dera_connectors.mysql_family.errors import map_mysql_family_error
from dera_connectors.mysql_family.security import (
    build_mysql_read_only_session_sql,
    build_mysql_ssl_context,
    validate_mysql_destination,
)
from dera_connectors.mysql_family.types import (
    MySqlTypeCategory,
    categorize_mysql_type,
    parse_column_type_attributes,
)

__all__ = [
    "MySqlFamilyConnectionManager",
    "MySqlTypeCategory",
    "build_mysql_read_only_session_sql",
    "build_mysql_ssl_context",
    "categorize_mysql_type",
    "introspect_check_constraints",
    "introspect_columns",
    "introspect_foreign_keys",
    "introspect_identity",
    "introspect_indexes",
    "introspect_primary_key",
    "introspect_schemas",
    "introspect_tables",
    "introspect_triggers",
    "introspect_unique_constraints",
    "introspect_views",
    "map_mysql_family_error",
    "parse_column_type_attributes",
    "validate_mysql_destination",
]
