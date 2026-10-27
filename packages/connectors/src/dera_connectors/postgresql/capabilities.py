"""DERA PostgreSQL Connector — Capability Matrix.

Defines the static and dynamic capability discovery models for standard PostgreSQL
and Supabase-hosted PostgreSQL instances.
"""

from dera_connectors.capabilities import (
    CapabilityStatus,
    CapabilitySupport,
    ConnectorCapabilities,
    ConnectorCapability,
)
from dera_connectors.engine import DatabaseEngine, DatabaseProvider


def get_postgres_capabilities(
    provider: DatabaseProvider = DatabaseProvider.GENERIC,
) -> ConnectorCapabilities:
    """Build and return the comprehensive capability matrix for PostgreSQL / Supabase."""
    caps: dict[ConnectorCapability, CapabilitySupport] = {
        ConnectorCapability.SCHEMA_ENUMERATION: CapabilitySupport(
            capability=ConnectorCapability.SCHEMA_ENUMERATION,
            status=CapabilityStatus.SUPPORTED,
            reason="Full pg_catalog.pg_namespace enumeration.",
        ),
        ConnectorCapability.TABLE_ENUMERATION: CapabilitySupport(
            capability=ConnectorCapability.TABLE_ENUMERATION,
            status=CapabilityStatus.SUPPORTED,
            reason="Relational tables, partitioned tables, and foreign tables via pg_catalog.pg_class.",
        ),
        ConnectorCapability.COLUMN_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.COLUMN_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Native types, nullability, default expressions, identity, generated columns, and collation.",
        ),
        ConnectorCapability.PRIMARY_KEY_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.PRIMARY_KEY_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Primary key constraints and composite key ordering via pg_constraint.",
        ),
        ConnectorCapability.FOREIGN_KEY_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.FOREIGN_KEY_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Foreign key relationships, composite keys, deferrability, and referential actions.",
        ),
        ConnectorCapability.UNIQUE_CONSTRAINT_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.UNIQUE_CONSTRAINT_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Unique constraints differentiated from secondary unique indexes.",
        ),
        ConnectorCapability.CHECK_CONSTRAINT_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.CHECK_CONSTRAINT_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Check constraints with untrusted check expressions extracted safely.",
        ),
        ConnectorCapability.INDEX_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.INDEX_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Access methods (BTREE, HASH, GIN, GIST, BRIN), partial filters, and expressions.",
        ),
        ConnectorCapability.VIEW_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.VIEW_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Standard SQL view definitions via pg_get_viewdef.",
        ),
        ConnectorCapability.MATERIALIZED_VIEW_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.MATERIALIZED_VIEW_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Materialized views differentiated from standard views.",
        ),
        ConnectorCapability.SEQUENCE_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.SEQUENCE_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Sequence metadata from pg_sequence without advancing sequence state.",
        ),
        ConnectorCapability.PARTITION_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.PARTITION_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Declarative partition bounds, keys, and parent-child hierarchy via pg_partitioned_table.",
        ),
        ConnectorCapability.COMMENT_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.COMMENT_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Catalog documentation comments via pg_description.",
        ),
        ConnectorCapability.TRIGGER_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.TRIGGER_INSPECTION,
            status=CapabilityStatus.SUPPORTED,
            reason="Trigger definition inspection without executing trigger functions.",
        ),
        ConnectorCapability.FUNCTION_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.FUNCTION_INSPECTION,
            status=CapabilityStatus.RESTRICTED,
            reason="Function and procedure introspection deferred to Phase 5.5 to prevent untrusted execution.",
        ),
        ConnectorCapability.PROCEDURE_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.PROCEDURE_INSPECTION,
            status=CapabilityStatus.RESTRICTED,
            reason="Procedure introspection deferred to Phase 5.5 to prevent untrusted execution.",
        ),
        ConnectorCapability.DEPENDENCY_INSPECTION: CapabilitySupport(
            capability=ConnectorCapability.DEPENDENCY_INSPECTION,
            status=CapabilityStatus.UNSUPPORTED,
            reason="Object dependency graph resolution scheduled for Phase 6 reverse-engineering engine.",
        ),
    }

    return ConnectorCapabilities(
        engine=DatabaseEngine.POSTGRESQL,
        capabilities=caps,
    )
