"""DERA MariaDB Connector Adapter.

Provides the production MariaDbConnector, configuration, and capabilities for MariaDB 10.11+
and 11.4 LTS database instances.
"""

from __future__ import annotations

from dera_connectors.mariadb.adapter import MariaDbConnector
from dera_connectors.mariadb.capabilities import get_mariadb_capabilities
from dera_connectors.mariadb.configuration import MariaDbConnectorConfig

__all__ = [
    "MariaDbConnector",
    "MariaDbConnectorConfig",
    "get_mariadb_capabilities",
]
