"""DERA SQLite Connector — Capability Matrix.

Defines the capability discovery model for SQLite 3.x embedded databases conforming
to DERA Phase 5.1 capability contracts.
"""

from dera_connectors.capabilities import (
    CapabilityStatus,
    CapabilitySupport,
    ConnectorCapabilities,
    ConnectorCapability,
)
from dera_connectors.engine import DatabaseEngine


def get_sqlite_capabilities() -> ConnectorCapabilities:
    """Build and return the comprehensive capability matrix for SQLite 3.x."""
    caps: dict[ConnectorCapability, CapabilitySupport] = {
        ConnectorCapability.SCHEMA_ENUMERATION: CapabilitySupport(
            capability=ConnectorCapability.SCHEMA_ENUMERATION,
            status=CapabilityStatus.SUPPORTED,
            reason="SQLite primary database namespace ('main') and PRAGMA database_list.",
        ),
        ConnectorCapability.TABLE_ENUMERATION: CapabilitySupport(
            capability=ConnectorCapability.TABLE_ENUMERATION,
            status=CapabilityStatus.SUPPORTED,
            reason="Tables, virtual tables, STRICT tables, and WITHOUT ROWID tables via sqlite_schema.",
        ),
        ConnectorCapability.COLUMN_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.COLUMN_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Column declarations, storage affinity, defaults, and generated/hidden flags via PRAGMA table_xinfo.",
        ),
        ConnectorCapability.PRIMARY_KEY_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.PRIMARY_KEY_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Single-column, composite, and INTEGER PRIMARY KEY rowid aliases.",
        ),
        ConnectorCapability.FOREIGN_KEY_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.FOREIGN_KEY_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Foreign key relationships and referential actions via PRAGMA foreign_key_list.",
        ),
        ConnectorCapability.UNIQUE_CONSTRAINT_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.UNIQUE_CONSTRAINT_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Unique constraints differentiated from explicit unique indexes via PRAGMA index_list.",
        ),
        ConnectorCapability.CHECK_CONSTRAINT_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.CHECK_CONSTRAINT_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Check constraints safely extracted from table DDL in sqlite_schema without execution.",
        ),
        ConnectorCapability.INDEX_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.INDEX_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Explicit, partial, expression, and unique indexes via PRAGMA index_list and index_xinfo.",
        ),
        ConnectorCapability.VIEW_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.VIEW_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Standard SQL view definitions from sqlite_schema without execution.",
        ),
        ConnectorCapability.TRIGGER_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.TRIGGER_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Database trigger definitions from sqlite_schema without execution.",
        ),
        ConnectorCapability.MATERIALIZED_VIEW_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.MATERIALIZED_VIEW_INSPECTION,
            status=CapabilityStatus.UNSUPPORTED,
            reason="SQLite 3 does not support materialized views.",
        ),
        ConnectorCapability.SEQUENCE_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.SEQUENCE_INSPECTION,
            status=CapabilityStatus.UNSUPPORTED,
            reason="SQLite 3 does not maintain standalone sequence objects.",
        ),
        ConnectorCapability.PARTITION_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.PARTITION_INSPECTION,
            status=CapabilityStatus.UNSUPPORTED,
            reason="SQLite 3 does not support declarative table partitioning.",
        ),
        ConnectorCapability.FUNCTION_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.FUNCTION_INSPECTION,
            status=CapabilityStatus.UNSUPPORTED,
            reason="SQLite functions are runtime C extensions, not stored database catalog metadata.",
        ),
        ConnectorCapability.PROCEDURE_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.PROCEDURE_INSPECTION,
            status=CapabilityStatus.UNSUPPORTED,
            reason="SQLite 3 does not support stored procedures.",
        ),
        ConnectorCapability.COMMENT_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.COMMENT_INSPECTION,
            status=CapabilityStatus.UNSUPPORTED,
            reason="Standard SQLite 3 does not maintain dedicated table or column comments.",
        ),
        ConnectorCapability.DEPENDENCY_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.DEPENDENCY_INSPECTION,
            status=CapabilityStatus.UNSUPPORTED,
            reason="SQLite 3 does not maintain an internal cross-object dependency graph catalog.",
        ),
    }

    return ConnectorCapabilities(
        engine=DatabaseEngine.SQLITE,
        capabilities=caps,
    )
