# Phase 5 Completion Audit: Database Connectors & Metadata Inspection

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Phase:** Phase 5 — Database Connectors & Metadata Inspection  
**Base Commit SHA:** `9d1be2d56f2c79a7030ee19af01ed62c2a1ec490`  
**Implementation Branch:** `security/phase-5.6-connector-safety`  
**Date:** October 27, 2026  
**Auditor:** Principal Database Architecture & Application Security Engineering Team  

---

## 1. Executive Summary

Phase 5 completes the core database connectivity, metadata catalog introspection, canonical normalization, and security qualification foundations of DERA. Over the course of six sequential engineering milestones (Phases 5.1 through 5.6), DERA has built a production-grade, deterministic, strongly typed database connector ecosystem capable of safely connecting to, inspecting, and canonically representing database schemas across:
- **PostgreSQL 13 - 17**
- **Supabase-hosted PostgreSQL**
- **SQLite 3.35+**
- **MySQL 8.0+**
- **MariaDB 10.5+**

In strict adherence to DERA's founding principles, the connector subsystem operates without artificial intelligence, large language models, or heuristic guessing. All transformations, object identities, query allowlists, and security boundaries are 100% deterministic, auditable, and fail closed.

---

## 2. Milestone Acceptance Status

| Milestone | Title | Focus & Core Deliverables | Acceptance Audit | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 5.1** | Universal Connector Protocol | Abstract `DatabaseConnector` interface, capability discovery registry, lifecycle manager, typed metadata contracts (`metadata.py`), conformance test suite. | [`PHASE_5_1_CONNECTOR_ACCEPTANCE.md`](PHASE_5_1_CONNECTOR_ACCEPTANCE.md) | **PASS** |
| **Phase 5.2** | PostgreSQL & Supabase Adapter | `asyncpg` native driver integration, system catalog queries (`pg_catalog`, `information_schema`), schema isolation, JSON/JSONB/Domain/Array types, Supabase pooler compatibility. | [`PHASE_5_2_POSTGRESQL_ACCEPTANCE.md`](PHASE_5_2_POSTGRESQL_ACCEPTANCE.md) | **PASS** |
| **Phase 5.3** | SQLite Adapter | `aiosqlite` integration, PRAGMA and `sqlite_master` catalog extraction, 5-rule SQLite type affinities, STRICT tables, WITHOUT ROWID tables, virtual columns, filesystem traversal protection. | [`PHASE_5_3_SQLITE_ACCEPTANCE.md`](PHASE_5_3_SQLITE_ACCEPTANCE.md) | **PASS** |
| **Phase 5.4** | MySQL & MariaDB Adapters | PyMySQL thread-pool execution, `INFORMATION_SCHEMA` metadata extraction, engine separation, ENUM/SET types, generated columns (`VIRTUAL` vs `STORED`), functional indexes, session read-only locking. | [`PHASE_5_4_MYSQL_MARIADB_ACCEPTANCE.md`](PHASE_5_4_MYSQL_MARIADB_ACCEPTANCE.md) | **PASS** |
| **Phase 5.5** | Canonical Metadata Normalization & Identity | Strongly typed canonical contracts (`dera.metadata`), 17 canonical type categories, cryptographic stable object identity (`ObjectId` via length-prefixed SHA-256), deterministic ordering, UTF-8 JSON serialization. | [`PHASE_5_5_METADATA_ACCEPTANCE.md`](PHASE_5_5_METADATA_ACCEPTANCE.md) | **PASS** |
| **Phase 5.6** | Read-Only Enforcement, Timeouts & Safety | Unified security policy, static lexical read-only enforcement, SSRF and port egress filters, DNS rebinding defense, SQLite filesystem containment, workspace isolation, centralized timeout budgets, cancellation tokens, structured audit logging. | [`PHASE_5_6_SECURITY_ACCEPTANCE.md`](PHASE_5_6_SECURITY_ACCEPTANCE.md) | **PASS** |

---

## 3. Connector Compatibility Matrix

| Database Engine | Minimum Supported Version | Connection Protocol | Read-Only Enforcement | Introspection Source | Capabilities Reported |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL** | 13.0+ | TCP / TLS via `asyncpg` | Session `READ ONLY`, statement timeouts | `pg_catalog`, `information_schema` | Schemas, Check Constraints, Domains, JSONB, Arrays, Partial Indexes |
| **Supabase PostgreSQL** | 15.0+ | TLS via PgBouncer / Direct | Session `READ ONLY`, statement timeouts | `pg_catalog`, `information_schema` | Same as PostgreSQL + Managed Connection Provider details |
| **SQLite** | 3.35+ | In-process via `aiosqlite` | URI `mode=ro`, `immutable=1` | `sqlite_master`, PRAGMA `table_xinfo`, etc. | STRICT, WITHOUT ROWID, Type Affinities, Virtual Columns |
| **MySQL** | 8.0+ | TCP / TLS via `pymysql` | Session `TRANSACTION READ ONLY` | `information_schema` | Invisible Indexes, Functional Key Parts, ENUM/SET, Expression Checks |
| **MariaDB** | 10.5+ | TCP / TLS via `pymysql` | Session `TRANSACTION READ ONLY` | `information_schema` | JSON Aliases, Persistent Generated Columns, Sequence Metadata |

---

## 4. Security & Safety Qualification Summary

The Phase 5.6 security qualification verified that all connector adapters operate within strict, bounded parameters:

1. **Strict Read-Only Guarantee:** Tested against 20+ mutation queries, comment injections, administrative functions, and file I/O escapes. 100% of mutation attempts failed closed before reaching customer databases.
2. **Network Egress Boundaries:** Tested against cloud metadata services (`169.254.169.254`, `metadata.google.internal`), loopback addresses, RFC 1918 subnets, and administrative ports. Zero unauthorized connections were permitted.
3. **Filesystem Containment:** Tested against path traversal (`../../etc/passwd`), null bytes, Windows device files (`CON`, `PRN`, `NUL`), and symlink escapes. All paths outside approved workspace roots were rejected.
4. **Tenant Isolation:** Tested against cross-workspace access attempts. Caller workspace must match target workspace before secrets are resolved or network sockets are opened.
5. **Timeouts & Cancellation:** Tested against monotonic deadlines and cooperative cancellation tokens. Operations abort promptly without leaving leaked connection handles.

---

## 5. Open Findings & Known Limitations

1. **Object Renames Across Snapshots (Phase 5.5):** Canonical object identity (`ObjectId`) is derived deterministically from canonical components including the native name. When a table or column is renamed in the source database, its `ObjectId` will change. Tracking object identity across renames is explicitly deferred to Phase 9 (Schema Comparison & Migration Engineering).
2. **Host-Level Egress Enforcement (Phase 5.6):** Application-level SSRF checks validate IP addresses and hostnames. However, defense-in-depth requires that production deployments also configure host/container network firewalls (e.g. AWS Security Groups, iptables) to prohibit outbound traffic to cloud metadata IP addresses at the kernel level.
3. **Large-Schema Memory Footprint:** Inspecting schemas with tens of thousands of tables requires bounded memory buffering. Resource limits (`max_result_rows = 50,000`, `max_metadata_objects = 100,000`) ensure memory consumption remains within safe operational boundaries.

---

## 6. Phase 6 Handoff Readiness

With Phase 5 complete, DERA possesses a verified foundation of database connectors, metadata extraction routines, canonical normalization contracts, stable object identities, and security controls.

The repository is now fully prepared for **Phase 6: Reverse Engineering Core Engine**, specifically:
- **Phase 6.1 — Canonical Schema Representation:** Transforming normalized canonical metadata into relational and topological models.
- **Phase 6.2 — Table & Constraint Analysis:** Reconstructing constraints, keys, and column rules.
- **Phase 6.3 — Relationship Discovery:** Inferring foreign key and naming-based associations.
- **Phase 6.4 — Dependency Graph Engine:** Constructing directed acyclic dependency graphs across tables, views, foreign keys, and triggers.
- **Phase 6.5 — Schema Snapshotting & Fingerprinting:** Capturing immutable schema state snapshots.

---

## 7. Overall Phase 5 Verdict

All requirements, architectural boundaries, connector adapters, canonical normalization contracts, security policies, adversarial test suites, and documentation deliverables across Milestones 5.1 through 5.6 have been completed and verified.

**Overall Phase 5 Verdict: PASS (READY FOR PHASE 6)**
