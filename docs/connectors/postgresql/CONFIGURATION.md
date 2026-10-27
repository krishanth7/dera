# PostgreSQL Connector Configuration Reference

## Configuration Schema

The connector uses `PostgresConnectorConfig` (inheriting from `ConnectorConfig`).

| Parameter | Type | Default | Description |
|---|---|---|---|
| `engine` | `DatabaseEngine` | `postgresql` | Fixed engine identifier. |
| `provider` | `DatabaseProvider` | `generic` | Provider designation (`generic`, `supabase`, `aws_rds`, `gcp_cloudsql`). |
| `database` | `str` | *Required* | Target database name. |
| `host` | `str` | *Required* | Database server hostname or IP address. |
| `port` | `int` | `5432` / `6543` | Listener port (5432 for direct, 6543 for Supabase poolers). |
| `username` | `str` | `None` | Authentication username. |
| `password` | `SecretStr` | `None` | Authentication password (auto-masked in logs and representation). |
| `credential_reference` | `str` | `None` | Vault or secret store reference for server-side secret resolution. |
| `application_name` | `str` | `DERA_Connector_v5.2` | Session identifier shown in `pg_stat_activity`. |
| `statement_timeout_ms` | `int` | `30000` | Session statement timeout in milliseconds (min: 1000, max: 600000). |
| `supabase_pooler_mode` | `SupabasePoolerMode` | `direct` | `direct`, `session`, or `transaction`. |
| `statement_cache_size` | `int` | `100` | Prepared statement cache size (automatically `0` in transaction pooler mode). |
| `tls` | `TLSSettings` | `TLSSettings()` | TLS configuration block. |
| `timeouts` | `TimeoutSettings` | `TimeoutSettings()` | Timeout boundaries block. |

---

## Example Usage

### Standard PostgreSQL Connection

```python
import uuid
from pydantic import SecretStr
from dera_connectors.context import ConnectorContext
from dera_connectors.postgresql import PostgresConnector, PostgresConnectorConfig

config = PostgresConnectorConfig(
    database="analytics_db",
    host="postgres.internal.mycompany.com",
    port=5432,
    username="dera_inspector",
    password=SecretStr("super_secret_password"),
    statement_timeout_ms=15000,
)

context = ConnectorContext(workspace_id=uuid.uuid4())

async with PostgresConnector(config=config, context=context) as connector:
    tables = await connector.list_tables(schema="public")
    for table in tables:
        print(f"Discovered: {table.qualified_name}")
```

### Supabase Connection (Transaction Pooler)

```python
config = PostgresConnectorConfig(
    database="postgres",
    host="aws-0-us-west-1.pooler.supabase.com",
    port=6543,
    username="postgres.my_project_ref",
    password=SecretStr("supabase_db_password"),
    supabase_pooler_mode="transaction",  # Automatically sets statement_cache_size=0
)
```
