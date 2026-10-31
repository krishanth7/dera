# Metadata Completeness & Provenance in ER Visualizations

**Document Reference**: `docs/frontend/ER_COMPLETENESS.md`  
**Milestone**: Phase 7.4 — Interactive ER Diagram Canvas & Relationship Visualization  

---

## 1. Completeness Status

Reverse-engineering extraction across database engines may encounter permission restrictions, catalog incompatibilities, or partial views. The diagram studio exposes metadata completeness in the `GraphStatus` banner:

| Status Badge | Meaning |
| :--- | :--- |
| **COMPLETE** | All foreign keys, columns, constraints, and namespaces were extracted and verified without catalog omissions. |
| **PARTIAL** | Certain system namespaces or catalog entries were omitted or restricted by database permissions. |
| **RESTRICTED**| Access to specific database catalogs was blocked by RBAC; visualized relationships represent a partial subset. |

---

## 2. Provenance Transparency

The canvas never displays synthetic or fabricated foreign keys. Every edge originates from authenticated database catalogs (e.g., `pg_constraint`, `information_schema.table_constraints`, `sqlite_master`).

The `GraphStatus` header displays:
- Active database name
- Target database engine badge (`postgresql`, `sqlite`, `mysql`, `mariadb`, `supabase`)
- Collection timestamp indicating when metadata was extracted
- Total verified table count and foreign key constraint count
