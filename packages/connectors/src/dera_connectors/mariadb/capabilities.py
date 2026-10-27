"""DERA MariaDB Connector — Capability Matrix.

Defines the capability discovery model for MariaDB 10.11+ and 11.4 LTS conforming to
DERA Phase 5.1 connector contracts.
"""

from __future__ import annotations

from dera_connectors.capabilities import (
    CapabilityStatus,
    CapabilitySupport,
    ConnectorCapabilities,
    ConnectorCapability,
)
from dera_connectors.engine import DatabaseEngine


def get_mariadb_capabilities() -> ConnectorCapabilities:
    """Build and return the comprehensive capability matrix for MariaDB 10.11+ and 11.4 LTS."""
    caps: dict[ConnectorCapability, CapabilitySupport] = {
        ConnectorCapability.SCHEMA_ENUMERATION: CapabilitySupport(
            capability=ConnectorCapability.SCHEMA_ENUMERATION,
            status=CapabilityStatus.SUPPORTED,
            reason="User database namespaces via INFORMATION_SCHEMA.SCHEMATA excluding system schemas.",
        ),
        ConnectorCapability.TABLE_ENUMERATION: CapabilitySupport(
            capability=ConnectorCapability.TABLE_ENUMERATION,
            status=CapabilityStatus.SUPPORTED,
            reason="Relational tables, views, Aria/InnoDB storage engines via INFORMATION_SCHEMA.TABLES.",
        ),
        ConnectorCapability.COLUMN_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.COLUMN_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Data types, nullability, defaults, auto_increment, virtual and persistent generated columns.",
        ),
        ConnectorCapability.PRIMARY_KEY_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.PRIMARY_KEY_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Primary key constraints and column order via INFORMATION_SCHEMA.KEY_COLUMN_USAGE.",
        ),
        ConnectorCapability.FOREIGN_KEY_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.FOREIGN_KEY_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Referential constraints, update/delete actions via INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS.",
        ),
        ConnectorCapability.UNIQUE_CONSTRAINT_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.UNIQUE_CONSTRAINT_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Unique constraints differentiated from primary keys via INFORMATION_SCHEMA.TABLE_CONSTRAINTS.",
        ),
        ConnectorCapability.CHECK_CONSTRAINT_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.CHECK_CONSTRAINT_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            version_introduced="10.2.1",
            reason="Check constraints via INFORMATION_SCHEMA.CHECK_CONSTRAINTS (MariaDB 10.2+).",
        ),
        ConnectorCapability.INDEX_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.INDEX_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="B-Tree, Hash, and invisible/ignored indexes via INFORMATION_SCHEMA.STATISTICS.",
        ),
        ConnectorCapability.VIEW_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.VIEW_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Standard SQL view definitions, check options, and security definers via INFORMATION_SCHEMA.VIEWS.",
        ),
        ConnectorCapability.TRIGGER_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.TRIGGER_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Trigger definitions, timings, and events via INFORMATION_SCHEMA.TRIGGERS without execution.",
        ),
        ConnectorCapability.COMMENT_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.COMMENT_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Table and column comments stored in MariaDB catalog metadata.",
        ),
        ConnectorCapability.MATERIALIZED_VIEW_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.MATERIALIZED_VIEW_INSPECTION,
            status=CapabilityStatus.UNSUPPORTED,
            reason="MariaDB does not support native materialized views.",
        ),
        ConnectorCapability.SEQUENCE_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.SEQUENCE_INSPECTION,
            status=CapabilityStatus.RESTRICTED,
            version_introduced="10.3.0",
            reason="MariaDB 10.3+ sequences require dedicated table/sequence inspection queries.",
        ),
        ConnectorCapability.PARTITION_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.PARTITION_INSPECTION,
            status=CapabilityStatus.RESTRICTED,
            reason="Partition metadata available via INFORMATION_SCHEMA.PARTITIONS for partitioned tables.",
        ),
        ConnectorCapability.FUNCTION_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.FUNCTION_INSPECTION,
            status=CapabilityStatus.UNSUPPORTED,
            reason="Stored function execution and introspection prohibited by platform policy.",
        ),
        ConnectorCapability.PROCEDURE_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.PROCEDURE_INSPECTION,
            status=CapabilityStatus.UNSUPPORTED,
            reason="Stored procedure execution and introspection prohibited by platform policy.",
        ),
        ConnectorCapability.DEPENDENCY_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.DEPENDENCY_INSPECTION,
            status=CapabilityStatus.UNSUPPORTED,
            reason="Cross-object dependency graphs not exposed natively in INFORMATION_SCHEMA.",
        ),
    }

    return ConnectorCapabilities(
        engine=DatabaseEngine.MARIADB,
        capabilities=caps,
    )
