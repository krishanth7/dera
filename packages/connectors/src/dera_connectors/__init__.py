"""DERA Connectors — Universal Database Connector & Capability Architecture.

Provides deterministic, read-only database introspection interfaces, capability
discovery, and connection lifecycles for PostgreSQL, SQLite, MySQL, and MariaDB.
"""

from dera_connectors.base.connector import (
    BaseConnector,
    ConnectionConfig,
)
from dera_connectors.capabilities import (
    CapabilityStatus,
    CapabilitySupport,
    ConnectorCapabilities,
    ConnectorCapability,
)
from dera_connectors.configuration import (
    ConnectorConfig,
    TimeoutSettings,
    TLSSettings,
)
from dera_connectors.context import (
    CancellationToken,
    ConnectorContext,
)
from dera_connectors.engine import (
    DatabaseEngine,
    DatabaseIdentity,
    DatabaseProvider,
)
from dera_connectors.errors import (
    ConnectorAuthenticationFailedError,
    ConnectorCancelledError,
    ConnectorConnectionLostError,
    ConnectorError,
    ConnectorErrorCode,
    ConnectorInvalidConfigurationError,
    ConnectorMetadataError,
    ConnectorPermissionDeniedError,
    ConnectorSecurityViolationError,
    ConnectorTimeoutError,
    ConnectorTLSError,
    ConnectorUnavailableError,
    ConnectorUnsupportedCapabilityError,
    ConnectorUnsupportedEngineError,
)
from dera_connectors.lifecycle import (
    ConnectionLifecycle,
    ConnectionState,
    InvalidLifecycleTransitionError,
)
from dera_connectors.metadata import (
    CheckConstraintInfo,
    ColumnInfo,
    ForeignKeyInfo,
    IndexInfo,
    PrimaryKeyInfo,
    SchemaInfo,
    TableInfo,
    UniqueConstraintInfo,
    ViewInfo,
)
from dera_connectors.protocol import DatabaseConnector
from dera_connectors.registry import (
    ConnectorRegistry,
    create_connector,
    default_connector_registry,
)
from dera_connectors.results import ConnectionTestResult
from dera_connectors.security import (
    ConnectorSecurityError,
    ReadOnlySecurityViolationError,
    SSRFSecurityViolationError,
    mask_sensitive_strings,
    sanitize_diagnostics,
    validate_network_target,
    validate_read_only_sql,
)
from dera_connectors.sqlite.connector import SqliteConnector

__version__ = "0.1.0-dev"

__all__ = [
    # Legacy interfaces
    "BaseConnector",
    "ConnectionConfig",
    "SqliteConnector",
    "__version__",
    # Protocol & engine
    "DatabaseConnector",
    "DatabaseEngine",
    "DatabaseIdentity",
    "DatabaseProvider",
    # Capabilities
    "ConnectorCapability",
    "CapabilityStatus",
    "CapabilitySupport",
    "ConnectorCapabilities",
    # Configuration & Context
    "ConnectorConfig",
    "TLSSettings",
    "TimeoutSettings",
    "ConnectorContext",
    "CancellationToken",
    # Lifecycle
    "ConnectionState",
    "ConnectionLifecycle",
    "InvalidLifecycleTransitionError",
    # Registry & Factory
    "ConnectorRegistry",
    "default_connector_registry",
    "create_connector",
    # Metadata contracts
    "SchemaInfo",
    "TableInfo",
    "ColumnInfo",
    "PrimaryKeyInfo",
    "ForeignKeyInfo",
    "UniqueConstraintInfo",
    "CheckConstraintInfo",
    "IndexInfo",
    "ViewInfo",
    # Results
    "ConnectionTestResult",
    # Errors
    "ConnectorError",
    "ConnectorErrorCode",
    "ConnectorUnavailableError",
    "ConnectorAuthenticationFailedError",
    "ConnectorPermissionDeniedError",
    "ConnectorTimeoutError",
    "ConnectorTLSError",
    "ConnectorUnsupportedEngineError",
    "ConnectorUnsupportedCapabilityError",
    "ConnectorInvalidConfigurationError",
    "ConnectorConnectionLostError",
    "ConnectorMetadataError",
    "ConnectorCancelledError",
    "ConnectorSecurityViolationError",
    # Security
    "ConnectorSecurityError",
    "ReadOnlySecurityViolationError",
    "SSRFSecurityViolationError",
    "mask_sensitive_strings",
    "sanitize_diagnostics",
    "validate_network_target",
    "validate_read_only_sql",
]
