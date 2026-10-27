# MySQL Connector Configuration

## Overview

The DERA MySQL Connector uses the strongly-typed `MySqlConnectorConfig` model (inheriting from `ConnectorConfig`). All parameters are validated at instantiation time using Pydantic v2. Raw connection strings and plaintext credentials are never accepted or logged.

---

## Configuration Properties

| Field | Type | Default | Description |
|---|---|---|---|
| `engine` | `DatabaseEngine` | `DatabaseEngine.MYSQL` | Must be `mysql`. Automatically enforced by model validator. |
| `database` | `str` | *(Required)* | Name of the default database / schema to inspect. |
| `host` | `str \| None` | `None` | Network hostname or IP address of the MySQL server. |
| `port` | `int \| None` | `3306` | TCP listener port. Defaults to 3306 if omitted. |
| `username` | `str \| None` | `None` | Database user account name for authentication. |
| `password` | `SecretStr \| None` | `None` | Password wrapped in `SecretStr` to prevent accidental logging. |
| `credential_reference` | `str \| None` | `None` | Vault or KMS secret identifier for server-side resolution. |
| `charset` | `str` | `"utf8mb4"` | Client character set encoding. |
| `tls` | `TLSSettings` | `TLSSettings()` | Transport layer security mode and certificate paths. |
| `timeouts` | `TimeoutSettings` | `TimeoutSettings()` | Bounded deadlines for connect, query, and overall scan operations. |
| `provider` | `DatabaseProvider` | `GENERIC` | Hosting platform (`GENERIC`, `AWS_RDS`, `AWS_AURORA`, `GCP_CLOUDSQL`). |

---

## Timeout Settings

`TimeoutSettings` ensures all network and query operations have strict execution deadlines:

- `connect_timeout_seconds`: 10.0s (min 0.5s, max 120.0s). Socket establishment and TLS negotiation deadline.
- `query_timeout_seconds`: 30.0s (min 0.5s, max 300.0s). Individual query deadline applied via `asyncio.wait_for` and `SET SESSION max_execution_time`.
- `total_deadline_seconds`: 60.0s (min 1.0s, max 600.0s). Overall deadline for composite schema scans.

---

## TLS Settings

`TLSSettings` controls encrypted transport:

- `ssl_mode`: `disable`, `require`, `verify-ca`, or `verify-full`.
- `ca_cert_path`: Optional path to custom Certificate Authority bundle.
- `client_cert_path`: Optional path to client certificate for mutual TLS (mTLS).
- `client_key_path`: Optional path to client private key for mTLS.
- `verify_hostname`: Boolean flag indicating whether server hostname must match certificate CN/SAN.

---

## Python Example

```python
import uuid
from pydantic import SecretStr
from dera_connectors.context import ConnectorContext
from dera_connectors.mysql import MySqlConnector, MySqlConnectorConfig

config = MySqlConnectorConfig(
    database="production_db",
    host="mysql-read-replica.internal",
    port=3306,
    username="dera_inspector",
    password=SecretStr("super-secure-password"),
)

context = ConnectorContext(workspace_id=uuid.uuid4())
connector = MySqlConnector(config=config, context=context)
```
