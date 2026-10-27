"""Connector Conformance Verification for FakeDatabaseConnector.

Verifies that FakeDatabaseConnector satisfies all requirements in BaseConnectorConformanceTests.
"""

import unittest

from dera_connectors.configuration import ConnectorConfig
from dera_connectors.context import ConnectorContext
from dera_connectors.engine import DatabaseEngine
from dera_connectors.protocol import DatabaseConnector
from dera_connectors.testing.conformance import BaseConnectorConformanceTests
from dera_connectors.testing.fake_connector import FakeDatabaseConnector


class TestFakeConnectorConformance(unittest.IsolatedAsyncioTestCase, BaseConnectorConformanceTests):
    """Executes the standard conformance suite against FakeDatabaseConnector."""

    def create_valid_config(self) -> ConnectorConfig:
        return ConnectorConfig(
            engine=DatabaseEngine.POSTGRESQL,
            host="fake-db.local",
            database="testdb",
        )

    def create_connector(
        self,
        config: ConnectorConfig | None = None,
        context: ConnectorContext | None = None,
    ) -> DatabaseConnector:
        cfg = config or self.create_valid_config()
        ctx = context or self.create_valid_context()
        return FakeDatabaseConnector(config=cfg, context=ctx)
