"""DERA Connectors — Connector Registry & Factory System.

Provides an explicit, static registry for database connector adapter classes.
Avoids dynamic import of arbitrary user modules and strictly rejects unknown database dialects.
"""

from dera_connectors.configuration import ConnectorConfig
from dera_connectors.context import ConnectorContext
from dera_connectors.engine import DatabaseEngine
from dera_connectors.errors import ConnectorUnsupportedEngineError
from dera_connectors.protocol import DatabaseConnector


class ConnectorRegistry:
    """Explicit, thread-safe registry mapping database engines to adapter classes."""

    def __init__(self) -> None:
        self._registry: dict[DatabaseEngine, type[DatabaseConnector]] = {}

    def register(self, engine: DatabaseEngine, connector_cls: type[DatabaseConnector]) -> None:
        """Register an adapter class for a specific database engine.

        Parameters
        ----------
        engine : DatabaseEngine
            The database engine family.
        connector_cls : Type[DatabaseConnector]
            The adapter class implementing DatabaseConnector.
        """
        self._registry[engine] = connector_cls

    def unregister(self, engine: DatabaseEngine) -> None:
        """Remove an adapter registration."""
        self._registry.pop(engine, None)

    def is_supported(self, engine: DatabaseEngine) -> bool:
        """Return True if an adapter is registered for this engine."""
        return engine in self._registry

    def list_supported_engines(self) -> list[DatabaseEngine]:
        """Return a sorted list of registered database engines."""
        return sorted(list(self._registry.keys()), key=lambda e: e.value)

    def get_connector_class(self, engine: DatabaseEngine) -> type[DatabaseConnector]:
        """Retrieve the adapter class for an engine or raise ConnectorUnsupportedEngineError."""
        if engine not in self._registry:
            raise ConnectorUnsupportedEngineError(
                engine=engine.value,
                message=f"No connector adapter registered for engine '{engine.value}'.",
            )
        return self._registry[engine]

    def create(
        self,
        config: ConnectorConfig,
        context: ConnectorContext,
    ) -> DatabaseConnector:
        """Instantiate a database connector instance without establishing a network connection.

        Parameters
        ----------
        config : ConnectorConfig
            Validated connector configuration.
        context : ConnectorContext
            Bound tenant and execution context.

        Returns
        -------
        DatabaseConnector
            Unconnected connector instance.
        """
        connector_cls = self.get_connector_class(config.engine)
        return connector_cls(config=config, context=context)


# Global default connector registry
default_connector_registry = ConnectorRegistry()

# Register standard adapters
from dera_connectors.postgresql.adapter import PostgresConnector  # noqa: E402

default_connector_registry.register(DatabaseEngine.POSTGRESQL, PostgresConnector)


def create_connector(
    config: ConnectorConfig,
    context: ConnectorContext,
    registry: ConnectorRegistry | None = None,
) -> DatabaseConnector:
    """Convenience factory function creating a connector instance from configuration and context."""
    active_registry = registry or default_connector_registry
    return active_registry.create(config=config, context=context)
