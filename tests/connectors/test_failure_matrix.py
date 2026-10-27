"""Failure and Edge-Case Test Matrix for DERA Connectors.

Validates:
- Network unavailability and authentication failure handling
- Catalog permission denial handling
- Bounded timeout detection and cooperative cancellation
- Lifecycle state transitions and illegal transition rejection
"""

import unittest
import uuid

from dera_connectors.configuration import ConnectorConfig
from dera_connectors.context import CancellationToken, ConnectorContext
from dera_connectors.engine import DatabaseEngine
from dera_connectors.errors import (
    ConnectorAuthenticationFailedError,
    ConnectorCancelledError,
    ConnectorPermissionDeniedError,
    ConnectorTimeoutError,
    ConnectorUnavailableError,
)
from dera_connectors.lifecycle import (
    ConnectionLifecycle,
    ConnectionState,
    InvalidLifecycleTransitionError,
)
from dera_connectors.testing.fake_connector import FakeDatabaseConnector


class TestConnectorFailureMatrix(unittest.IsolatedAsyncioTestCase):
    """Test suite validating failure modes and resilient teardown in connector adapters."""

    def setUp(self) -> None:
        self.config = ConnectorConfig(
            engine=DatabaseEngine.POSTGRESQL,
            host="postgres.failure-test.local",
            database="testdb",
        )
        self.context = ConnectorContext(workspace_id=uuid.uuid4())

    async def test_simulate_connection_failure(self) -> None:
        """Verify unreachable host raises ConnectorUnavailableError and transitions to FAILED."""
        connector = FakeDatabaseConnector(
            config=self.config,
            context=self.context,
            simulate_connect_failure=True,
        )
        with self.assertRaises(ConnectorUnavailableError):
            await connector.connect()

        self.assertEqual(connector.state, ConnectionState.FAILED)

        # Ensure close cleans up gracefully from FAILED state
        await connector.close()
        self.assertEqual(connector.state, ConnectionState.CLOSED)

    async def test_simulate_authentication_failure(self) -> None:
        """Verify rejected credentials raise ConnectorAuthenticationFailedError."""
        connector = FakeDatabaseConnector(
            config=self.config,
            context=self.context,
            simulate_auth_failure=True,
        )
        with self.assertRaises(ConnectorAuthenticationFailedError):
            await connector.connect()

        self.assertEqual(connector.state, ConnectionState.FAILED)

    async def test_simulate_permission_denial(self) -> None:
        """Verify catalog inspection raises ConnectorPermissionDeniedError when grants are missing."""
        connector = FakeDatabaseConnector(
            config=self.config,
            context=self.context,
            simulate_permission_denial=True,
        )
        await connector.connect()
        self.assertEqual(connector.state, ConnectionState.CONNECTED)

        with self.assertRaises(ConnectorPermissionDeniedError):
            await connector.list_tables()

        await connector.close()
        self.assertEqual(connector.state, ConnectionState.CLOSED)

    async def test_simulate_timeout(self) -> None:
        """Verify operation timeout raises ConnectorTimeoutError."""
        connector = FakeDatabaseConnector(
            config=self.config,
            context=self.context,
            simulate_timeout=True,
        )
        with self.assertRaises(ConnectorTimeoutError):
            await connector.connect()

        self.assertEqual(connector.state, ConnectionState.FAILED)

    async def test_simulate_cancellation_during_active_connection(self) -> None:
        """Verify cooperative cancellation token aborts active operations."""
        token = CancellationToken()
        ctx = ConnectorContext(workspace_id=uuid.uuid4(), cancellation_token=token)
        connector = FakeDatabaseConnector(config=self.config, context=ctx)

        await connector.connect()
        self.assertEqual(connector.state, ConnectionState.CONNECTED)

        # Trigger cancellation
        token.cancel("User aborted scan.")

        with self.assertRaises(ConnectorCancelledError):
            await connector.list_tables()

        await connector.close()

    def test_lifecycle_illegal_transitions_rejected(self) -> None:
        """Verify invalid lifecycle transitions raise InvalidLifecycleTransitionError."""
        lifecycle = ConnectionLifecycle()
        self.assertEqual(lifecycle.state, ConnectionState.CREATED)

        # Cannot jump directly from CREATED to CONNECTED (must go through CONNECTING)
        with self.assertRaises(InvalidLifecycleTransitionError):
            lifecycle.transition_to(ConnectionState.CONNECTED)

        # Transition to CONNECTING
        lifecycle.transition_to(ConnectionState.CONNECTING)

        # Transition to CONNECTED
        lifecycle.transition_to(ConnectionState.CONNECTED)

        # Cannot jump back from CONNECTED to CREATED
        with self.assertRaises(InvalidLifecycleTransitionError):
            lifecycle.transition_to(ConnectionState.CREATED)

        # Transition to CLOSING and CLOSED
        lifecycle.transition_to(ConnectionState.CLOSING)
        lifecycle.transition_to(ConnectionState.CLOSED)

        # Cannot resurrect from CLOSED
        with self.assertRaises(InvalidLifecycleTransitionError):
            lifecycle.transition_to(ConnectionState.CONNECTING)
