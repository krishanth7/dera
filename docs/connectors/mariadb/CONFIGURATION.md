# MariaDB Connector Configuration

## Overview

The DERA MariaDB Connector uses the strongly-typed `MariaDbConnectorConfig` model (inheriting from `ConnectorConfig`). All parameters are validated at instantiation time using Pydantic v2. Raw connection strings and plaintext credentials are never accepted or logged.

---

## Configuration Properties

| Field | Type | Default | Description |
|---|---|---|---|
| `engine` | `DatabaseEngine` | `DatabaseEngine.MARIADB` | Must be `mariadb`. Automatically enforced by model validator. |
| `database` | `str` | *(Required)* | Name of the default database / schema to inspect. |
| `host` | `str \| None` | `None` | Network hostname or IP address of the MariaDB server. |
| `port` | `int \| None` | `3306` | TCP listener port. Defaults to 3306 if omitted. |
| `username` | `str \| None` | `None` | Database user account name for authentication. |
| `password` | `SecretStr \| None` | `None` | Password wrapped in `SecretStr` to prevent accidental logging. |
| `credential_reference` | `str \| None` | `None` | Vault or KMS secret identifier for server-side resolution. |
| `charset` | `str` | `"utf8mb4"` | Client character set encoding. |
| `tls` | `TLSSettings` | `TLSSettings()` | Transport layer security mode and certificate paths. |
| `timeouts` | `TimeoutSettings` | `TimeoutSettings()` | Bounded deadlines for connect, query, and overall scan operations. |
| `provider` | `DatabaseProvider` | `GENERIC` | Hosting platform (`GENERIC`, `AWS_RDS`, etc.). |

---

## Timeout Settings

`TimeoutSettings` ensures all network and query operations have strict execution deadlines:

- `connect_timeout_seconds`: 10.0s (min 0.5s, max 120.0s). Socket establishment and TLS negotiation deadline.
- `query_timeout_seconds`: 30.0s (min 0.5s, max 300.0s). Individual query deadline applied via `asyncio.wait_for` and `SET SESSION max_statement_time`.
- `total_deadline_seconds`: 60.0s (min 1.0s, max 600.0s). Overall deadline for composite schema scans.

---

## Python Example

```python
import uuid
from pydantic import SecretStr
from dera_connectors.context import ConnectorContext
from dera_connectors.mariadb import MariaDbConnector, MariaDbConnectorConfig

config = MariaDbConnectorConfig(
    database="warehouse_db",
    host="mariadb-node-1.internal",
    port=3306,
    username="dera_inspector",
    password=SecretStr("super-secure-password"),
)

context = ConnectorContext(workspace_id=uuid.uuid4())
connector = MariaDbConnector(config=config, context=context)
```
