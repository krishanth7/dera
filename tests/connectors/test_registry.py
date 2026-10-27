"""Unit Tests for DERA Connector Registry and Adapter Factory.

Validates:
- Explicit driver registration and engine mapping
- Unsupported engine rejection
- Factory instantiation without premature connection
"""

import unittest
import uuid

from dera_connectors.configuration import ConnectorConfig
from dera_connectors.context import ConnectorContext
from dera_connectors.engine import DatabaseEngine
from dera_connectors.errors import ConnectorUnsupportedEngineError
from dera_connectors.lifecycle import ConnectionState
from dera_connectors.registry import ConnectorRegistry, create_connector
from dera_connectors.testing.fake_connector import FakeDatabaseConnector


class TestConnectorRegistry(unittest.TestCase):
    """Test suite validating ConnectorRegistry and adapter factory operations."""

    def setUp(self) -> None:
        self.registry = ConnectorRegistry()
        self.config = ConnectorConfig(
            engine=DatabaseEngine.POSTGRESQL,
            host="postgres.local",
            database="appdb",
        )
        self.context = ConnectorContext(workspace_id=uuid.uuid4())

    def test_register_and_create_connector(self) -> None:
        """Verify registering an engine allows successful factory creation."""
        self.assertFalse(self.registry.is_supported(DatabaseEngine.POSTGRESQL))

        self.registry.register(DatabaseEngine.POSTGRESQL, FakeDatabaseConnector)
        self.assertTrue(self.registry.is_supported(DatabaseEngine.POSTGRESQL))
        self.assertIn(DatabaseEngine.POSTGRESQL, self.registry.list_supported_engines())

        # Factory creation
        connector = self.registry.create(config=self.config, context=self.context)
        self.assertIsInstance(connector, FakeDatabaseConnector)
        self.assertEqual(connector.state, ConnectionState.CREATED)

    def test_unsupported_engine_raises_error(self) -> None:
        """Verify requesting an unregistered engine raises ConnectorUnsupportedEngineError."""
        with self.assertRaises(ConnectorUnsupportedEngineError) as ctx:
            self.registry.get_connector_class(DatabaseEngine.MYSQL)

        self.assertEqual(ctx.exception.details["requested_engine"], "mysql")

    def test_convenience_create_connector_function(self) -> None:
        """Verify module-level create_connector helper routes through the active registry."""
        self.registry.register(DatabaseEngine.POSTGRESQL, FakeDatabaseConnector)

        connector = create_connector(
            config=self.config,
            context=self.context,
            registry=self.registry,
        )
        self.assertEqual(connector.config.database, "appdb")
        self.assertEqual(connector.state, ConnectionState.CREATED)
