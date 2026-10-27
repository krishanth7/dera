# Connector Conformance Testing Guide

## Purpose

The `BaseConnectorConformanceTests` suite (`packages/connectors/src/dera_connectors/testing/conformance.py`) defines a reusable battery of unit tests that every database adapter must inherit and satisfy.

## Test Matrix

1. `test_protocol_conformance`: Asserts adapter satisfies `isinstance(adapter, DatabaseConnector)`.
2. `test_lifecycle_connect_and_close`: Validates transitions from `CREATED` to `CONNECTED` and terminal `CLOSED`, including idempotent `close()`.
3. `test_async_context_manager`: Validates automatic connect and cleanup with `async with`.
4. `test_identity_and_capabilities`: Validates `DatabaseIdentity` structure and capability discovery mapping.
5. `test_deterministic_table_ordering`: Verifies table list is sorted by `(schema_name, table_name)`.
6. `test_deterministic_column_ordering`: Verifies column list is sorted by `ordinal_position`.
7. `test_cancellation_responsiveness`: Verifies `CancellationToken.is_cancelled` aborts connections with `ConnectorCancelledError`.
8. `test_no_mutation_apis_on_protocol`: Asserts no mutation methods (`execute`, `insert`, etc.) exist on the object.

## Example Implementation for New Adapter

```python
from dera_connectors.testing.conformance import BaseConnectorConformanceTests


class TestMyAdapterConformance(unittest.IsolatedAsyncioTestCase, BaseConnectorConformanceTests):
    def create_valid_config(self) -> ConnectorConfig:
        return ConnectorConfig(engine=DatabaseEngine.POSTGRESQL, host="localhost", database="test")

    def create_connector(self, config=None, context=None):
        return MyDatabaseConnector(
            config=config or self.create_valid_config(),
            context=context or self.create_valid_context(),
        )
```
