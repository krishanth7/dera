# DERA Platform Database & Migrations Documentation

Welcome to the authoritative persistence documentation for DERA (Database Engineering & Reverse Analysis).

## Overview

DERA Phase 4.3 establishes the authoritative internal platform PostgreSQL persistence layer, asynchronous engine management, connection pooling, Alembic migration framework, declarative models, and repository abstractions.

> **CRITICAL ARCHITECTURAL SEPARATION**:
> The internal platform database documented here is strictly isolated from customer databases inspected by DERA in Phase 5+.
> Platform migrations NEVER execute against customer databases, and customer connections are NEVER reused for platform persistence.

---

## Documentation Index

| Document | Description |
| :--- | :--- |
| [Architecture](ARCHITECTURE.md) | Architectural domains, strict separation invariant, and component lifecycle. |
| [Configuration](CONFIGURATION.md) | Validated environment variables, pooling parameters, timeouts, and credential masking. |
| [Local PostgreSQL Setup](LOCAL_POSTGRESQL.md) | Reproducible local development using Docker Compose and PostgreSQL 16. |
| [SQLAlchemy Guide](SQLALCHEMY_GUIDE.md) | SQLAlchemy 2.x DeclarativeBase, naming conventions, mapped columns, and session scopes. |
| [Migration Policy](MIGRATION_POLICY.md) | Alembic async workflow, autogeneration review, risk classification, and zero-downtime guidelines. |
| [Transaction Policy](TRANSACTION_POLICY.md) | Atomic write boundaries, `transaction_scope`, explicit commits, and automatic rollbacks. |
| [Security & Roles](SECURITY_AND_ROLES.md) | Principle of least privilege, role separation (migration vs. runtime), TLS, and secret protection. |
| [Testing Guide](TESTING.md) | Unit, session, constraint, transaction, health probe, and PostgreSQL integration testing. |
| [Disaster Recovery](RECOVERY.md) | Schema drift detection, backup strategies, downgrade limitations, and recovery protocols. |

---

## Core Technologies

- **Database Engine**: PostgreSQL 16+
- **ORM & Core**: SQLAlchemy 2.x (Asyncio extension)
- **Async Driver**: `asyncpg` (Production & CI), `aiosqlite` (In-memory testing)
- **Migration Engine**: Alembic 1.13+ with async runner
- **Application Framework**: FastAPI with lifespan-managed connection pooling
- **Validation**: Pydantic v2 Settings with credential masking
