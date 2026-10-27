# MariaDB Connector Capability Matrix

## Overview

The DERA MariaDB Connector implements Phase 5.1 capability contracts. Capabilities are classified as `SUPPORTED`, `RESTRICTED`, or `UNSUPPORTED`.

---

## Capability Status Declarations

| Capability | Status | Version / Rationale |
|---|---|---|
| `schema_enumeration` | `SUPPORTED` | `INFORMATION_SCHEMA.SCHEMATA` excluding internal administrative schemas (`information_schema`, `performance_schema`, `mysql`, `sys`). |
| `table_enumeration` | `SUPPORTED` | Base tables and views via `INFORMATION_SCHEMA.TABLES` with Aria/InnoDB engine support. |
| `column_inspection` | `SUPPORTED` | Full column definitions, auto_increment, virtual and persistent generated columns via `INFORMATION_SCHEMA.COLUMNS`. |
| `primary_key_inspection` | `SUPPORTED` | `PRIMARY` key discovery and column order via `INFORMATION_SCHEMA.KEY_COLUMN_USAGE`. |
| `foreign_key_inspection` | `SUPPORTED` | Referential actions (`ON UPDATE`, `ON DELETE`) via `INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS`. |
| `unique_constraint_inspection` | `SUPPORTED` | Unique constraints distinguished from primary keys via `INFORMATION_SCHEMA.TABLE_CONSTRAINTS`. |
| `check_constraint_inspection` | `SUPPORTED` | Supported in MariaDB 10.2+ via `INFORMATION_SCHEMA.CHECK_CONSTRAINTS`. |
| `index_inspection` | `SUPPORTED` | Secondary indexes, composite indexes, and invisible/ignored indexes via `INFORMATION_SCHEMA.STATISTICS`. |
| `view_inspection` | `SUPPORTED` | View definitions, check options, and definer attributes via `INFORMATION_SCHEMA.VIEWS`. |
| `trigger_inspection` | `SUPPORTED` | Trigger timings, events, and action statements via `INFORMATION_SCHEMA.TRIGGERS`. |
| `comment_inspection` | `SUPPORTED` | Table comments and column comments stored in catalog metadata. |
| `materialized_view_inspection` | `UNSUPPORTED` | MariaDB does not support native materialized views. |
| `sequence_inspection` | `RESTRICTED` | MariaDB 10.3+ sequences require dedicated table/sequence inspection queries. |
| `partition_inspection` | `RESTRICTED` | Partition metadata accessible via `INFORMATION_SCHEMA.PARTITIONS` for partitioned tables. |
| `function_inspection` | `UNSUPPORTED` | Stored function execution and routine introspection prohibited by platform policy. |
| `procedure_inspection` | `UNSUPPORTED` | Stored procedure execution and routine introspection prohibited by platform policy. |
| `dependency_inspection` | `UNSUPPORTED` | Cross-object dependency graphs not exposed natively in MariaDB catalogs. |
