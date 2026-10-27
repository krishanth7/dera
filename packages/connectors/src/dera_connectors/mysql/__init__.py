"""DERA MySQL Connector Adapter.

Provides the production MySqlConnector, configuration, and capabilities for MySQL 8.0+
and 8.4 LTS database instances.
"""

from __future__ import annotations

from dera_connectors.mysql.adapter import MySqlConnector
from dera_connectors.mysql.capabilities import get_mysql_capabilities
from dera_connectors.mysql.configuration import MySqlConnectorConfig

__all__ = [
    "MySqlConnector",
    "MySqlConnectorConfig",
    "get_mysql_capabilities",
]
