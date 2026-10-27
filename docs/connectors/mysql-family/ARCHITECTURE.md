# MySQL-Family Connector Architecture

## Architectural Vision

The DERA MySQL-Family connector subsystem provides a unified, highly optimized foundation for both MySQL and MariaDB adapters. While sharing the underlying wire protocol and `INFORMATION_SCHEMA` structure, the architecture explicitly avoids erasing critical distinctions between the two database engines.

```text
+--------------------------------------------------------------------+
|                         DERA Platform                              |
|             (FastAPI / Background Jobs / Tenant Context)           |
+--------------------------------------------------------------------+
                                  |
                                  v
+--------------------------------------------------------------------+
|                    Universal Connector Protocol                    |
|                (Phase 5.1 DatabaseConnector Interface)             |
+--------------------------------------------------------------------+
                 |                                  |
                 v                                  v
+----------------------------------+ +-------------------------------+
|          MySQL Adapter           | |        MariaDB Adapter        |
|        (`MySqlConnector`)        | |      (`MariaDbConnector`)     |
+----------------------------------+ +-------------------------------+
                 \                                  /
                  \                                /
                   v                              v
+--------------------------------------------------------------------+
|                    Shared MySQL-Family Subsystem                   |
|                   (`dera_connectors.mysql_family`)                 |
|                                                                    |
|  - `connection.py`: Thread-pool async bridging via asyncio.to_thread|
|  - `security.py`: SSRF, loopback policy, TLS context, read-only SQL|
|  - `catalog.py`: Pre-reviewed, parameterized INFORMATION_SCHEMA queries|
|  - `types.py`: Native type preservation, unsigned/zerofill, enums |
|  - `errors.py`: Sanitized error mapping to ConnectorError taxonomy |
+--------------------------------------------------------------------+
                                  |
                                  v
+--------------------------------------------------------------------+
|                      PyMySQL Driver & Network                      |
|                  (Pure Python, TLS 1.2+, Threaded)                 |
+--------------------------------------------------------------------+
```

---

## Driver Selection & Rationale

We evaluated several Python drivers for the MySQL wire protocol:

1. **`PyMySQL` (Selected):** Pure Python, zero binary compilation hazards, fully compatible with Windows, macOS, and Linux across ARM64 and x86_64. Integrates seamlessly with `asyncio.to_thread` for non-blocking I/O, supports TLS via standard `ssl.SSLContext`, and maintains excellent stability.
2. **`mysqlclient`:** Fast C-extension, but requires `libmysqlclient-dev` / C toolchains, causing installation and portability hazards across diverse container and developer environments.
3. **`asyncmy`:** Async driver using native coroutines, but has historical maintenance gaps, smaller community adoption, and edge-case TLS handshake bugs.
4. **`mysql-connector-python`:** Heavyweight, proprietary licensing edge cases, and complex dependencies.

`PyMySQL` combined with `asyncio.to_thread` and strict cooperative cancellation provides the optimal balance of safety, portability, performance, and maintenance.

---

## Dialect & Engine Differentiation

The shared layer preserves engine identity and behavior:

- **Engine Identification:** Introspects `VERSION()` and `@@version_comment`. If `"MariaDB"` is detected, the engine is classified as `DatabaseEngine.MARIADB`; otherwise `DatabaseEngine.MYSQL`.
- **Query Timeouts:** MySQL uses `SET SESSION max_execution_time = {ms};` while MariaDB uses `SET SESSION max_statement_time = {seconds};`.
- **Check Constraints:** MySQL 8.0.16+ joins `TABLE_CONSTRAINTS` with `CHECK_CONSTRAINTS`, while MariaDB uses `CHECK_CONSTRAINTS` directly.
- **Index Expressions:** MySQL 8.0+ supports expression terms (`EXPRESSION`) in `INFORMATION_SCHEMA.STATISTICS`, while MariaDB statistics queries handle standard terms.
- **Generated Columns:** MariaDB uses `PERSISTENT` and `VIRTUAL`, while MySQL uses `STORED` and `VIRTUAL`. Both are mapped to normalized `ColumnInfo` models.
