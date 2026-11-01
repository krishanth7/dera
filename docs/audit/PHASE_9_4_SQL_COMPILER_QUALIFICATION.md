# Phase 9.4 SQL Compiler Qualification Report

## 1. Executive Summary
- **Component**: `packages/core/src/dera/migration/sql/`
- **Milestone**: 9.4 — Migration SQL Generation & Dialect-Aware Validation
- **Status**: **PASS (Verified)**
- **Audit Focus**: Dialect Matrix, Identifier Quoting & Injection Safety, Transaction Boundaries, Review-Only Guarantees.

---

## 2. Dialect Capability Matrix

| Operation | PostgreSQL | SQLite | MySQL | MariaDB | Enforcement & Behavior |
|:---|:---:|:---:|:---:|:---:|:---|
| **CREATE TABLE** | Supported | Supported | Supported | Supported | Full column definitions, primary keys, and types |
| **DROP TABLE** | Supported | Supported | Supported | Supported | Emits high-risk warnings; requires explicit manual review gate |
| **ADD COLUMN** | Supported | Supported | Supported | Supported | Handled with nullability and default-value checks |
| **DROP COLUMN** | Supported | Limitations | Supported | Supported | SQLite warns on older versions; emits destructive warnings |
| **CREATE INDEX** | Supported | Supported | Supported | Supported | Fully qualified with table reference and dialect quoting |
| **DROP INDEX** | Supported | Supported | Supported | Supported | Clean index removal statements |
| **FOREIGN KEY ADD** | Supported | Manual Review | Supported | Supported | SQLite requires table recreation pattern for constraint addition |
| **TRANSACTION DDL** | Supported | Supported | Not Supported | Not Supported | MySQL/MariaDB implicitly commit DDL; warnings emitted |

---

## 3. SQL Safety & Injection Protection

### 3.1 Identifier Quoting
- **PostgreSQL / SQLite**: Uses standard double quotes (`"identifier"`), escaping internal double quotes by doubling (`""`).
- **MySQL / MariaDB**: Uses backticks (`` `identifier` ``), escaping internal backticks by doubling (`` `` ``).
- **Reserved Keywords**: All identifiers (table names, column names, constraint names) are unconditionally quoted across all dialects, completely neutralizing SQL injection via identifier names.

### 3.2 Review-Only Safeguards
- **Header Notice**: Every compiled artifact begins with:
  ```sql
  -- DERA GENERATED MIGRATION ARTIFACT
  -- NOTICE: GENERATED FOR REVIEW — NOT EXECUTED
  -- DO NOT EXECUTE DIRECTLY WITHOUT PRIOR REVIEW AND APPROVAL
  ```
- **Read-Only Architecture**: Customer database connectors in `packages/core/src/dera/connectors/` are strictly configured for read-only introspective access (`autocommit=False`, `SET TRANSACTION READ ONLY`). No execution API exists in DERA to run migration SQL against customer targets.
