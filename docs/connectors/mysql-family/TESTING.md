# MySQL-Family Testing Strategy & Evidence

## Overview

DERA mandates comprehensive automated testing for all connector adapters across unit, conformance, security, and live integration dimensions.

---

## Test Suites Overview

### 1. Conformance Testing (`BaseConnectorConformanceTests`)

Both `MySqlConnector` and `MariaDbConnector` inherit and independently satisfy `BaseConnectorConformanceTests`:

- Protocol compliance: implements `DatabaseConnector` interface methods.
- Lifecycle: validates `CREATED` -> `CONNECTED` -> `CLOSED` state machine transitions.
- Idempotence: repeated calls to `close()` remain safe and idempotent.
- Context Manager: `async with connector as conn:` automatically connects and tears down.
- Identity & Capabilities: returns strongly-typed `DatabaseIdentity` and `ConnectorCapabilities`.
- Deterministic Ordering: validates tables sorted by `(schema, table)` and columns sorted by `ordinal_position`.

### 2. Unit Testing (`tests/connectors/mysql_family/`)

- `test_configuration.py`: Verifies typed configs, port defaults (3306), character set (utf8mb4), credential masking, and TLS paths.
- `test_security.py`: Verifies SSRF destination blocking, loopback access policies, cloud metadata blocking (`169.254.169.254`), TLS context construction, and read-only session SQL generation.
- `test_errors.py`: Tests error mapping for error numbers 1045, 1044, 2002, 2003, 2026, 3024, 1317 to Phase 5.1 `ConnectorError` subclasses.
- `test_types.py`: Tests data type categorization across integer, decimal, string, binary, temporal, spatial, json, enum, and set types, plus `tinyint(1)` boolean aliases and unsigned flags.

### 3. Engine-Specific Adapter Tests

- `tests/connectors/mysql/test_mysql_adapter.py`: Mock MySQL 8.0 manager testing identity detection, functional indexes (`upper(username)`), stored generated columns, check constraints, foreign keys, and triggers.
- `tests/connectors/mariadb/test_mariadb_adapter.py`: Mock MariaDB 10.11 manager testing MariaDB engine identification, `Aria` and `InnoDB` storage engines, `PERSISTENT GENERATED` columns, and check constraint fallbacks.

### 4. Live Integration & Read-Only Tests

- `tests/integration/mysql/test_mysql_live.py`: Verifies read-only mutation rejection on `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `ALTER`, `DROP`, `TRUNCATE`, `GRANT`, `REVOKE` statements, and live fixture querying when configured.
- `tests/integration/mariadb/test_mariadb_live.py`: Verifies read-only mutation rejection and MariaDB catalog verification.

---

## Running Test Suites

Execute all connector tests:
```bash
python -m unittest discover tests/connectors
```

Execute all integration tests:
```bash
python -m unittest discover tests/integration
```

Execute full repository test suite:
```bash
python -m unittest discover tests
```
