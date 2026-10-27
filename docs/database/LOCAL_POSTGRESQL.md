# Local PostgreSQL Setup for Development & Testing

DERA provides a reproducible, non-production Docker Compose configuration for local database development.

---

## 1. Quickstart

To spin up the local development PostgreSQL 16 container:

```bash
docker compose -f docker-compose.db.yml up -d
```

To verify the container is healthy:

```bash
docker compose -f docker-compose.db.yml ps
```

To stop the container:

```bash
docker compose -f docker-compose.db.yml down
```

To stop the container and wipe all persisted development volume data:

```bash
docker compose -f docker-compose.db.yml down -v
```

---

## 2. Local Container Parameters

| Setting | Value |
| :--- | :--- |
| **Image** | `postgres:16-alpine` |
| **Container Name** | `dera-platform-db` |
| **Host Binding** | `127.0.0.1:5432` (strictly bound to loopback; never exposed publicly) |
| **Database Name** | `dera_platform` |
| **Username** | `dera_user` |
| **Password** | `dera_password` (ephemeral development only) |
| **Volume** | `dera_platform_pgdata` |

---

## 3. Connecting Your Local API

Configure your `.env` file in `apps/api/.env`:

```bash
DERA_PLATFORM_DATABASE_URL="postgresql+asyncpg://dera_user:dera_password@127.0.0.1:5432/dera_platform"
```

Then apply the latest platform schema migrations:

```bash
alembic upgrade head
```

Verify the current migration status:

```bash
alembic current
```
