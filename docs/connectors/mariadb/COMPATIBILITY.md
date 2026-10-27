# MariaDB Version Compatibility Matrix

## Supported Engine Releases

The DERA MariaDB Connector targets modern MariaDB database engine releases with verifiable integration test coverage:

| Engine Version | Release Type | Support Status | Key Behavioral Characteristics |
|---|---|---|---|
| **MariaDB 11.4 LTS** | Long-Term Support | Supported | Modern optimizer, enhanced `CHECK_CONSTRAINTS`, `PERSISTENT` generated columns, strict SQL mode. |
| **MariaDB 10.11 LTS** | Long-Term Support | Supported | Stable LTS baseline, `Aria` and `InnoDB` engines, `max_statement_time` session variable. |
| **MariaDB 10.5 LTS** | Maintenance | Supported | Base `CHECK_CONSTRAINTS` catalog support, virtual/persistent columns. |

---

## Dialect and Driver Compatibility

- **Driver:** `PyMySQL` (>=1.1.0) pure Python driver.
- **Python Runtimes:** Python 3.12, 3.13.
- **TLS Protocols:** TLS 1.2, TLS 1.3 enforced by `ssl.SSLContext`.
- **Operating Systems:** Linux (Ubuntu 22.04+), macOS (13+), Windows 10/11 / Windows Server 2022.
- **Authentication Plugins:** `mysql_native_password`, `ed25519`.

---

## Engine Differences from MySQL

- **Engine Identification:** MariaDB server version string and `@@version_comment` contain `"MariaDB"`. The connector correctly sets `DatabaseEngine.MARIADB`.
- **Statement Timeout:** Uses `SET SESSION max_statement_time = {seconds};` rather than MySQL's `max_execution_time` (which expects milliseconds).
- **Generated Columns:** MariaDB supports `VIRTUAL` and `PERSISTENT`, while MySQL uses `VIRTUAL` and `STORED`. Both map to standard DERA models.
