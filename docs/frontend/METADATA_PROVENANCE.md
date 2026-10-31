# Metadata Provenance Specification

**Document Reference**: `docs/frontend/METADATA_PROVENANCE.md`  
**Milestone**: Phase 7.3 — Database Connection & Schema Explorer UI  

---

## 1. Extraction Provenance Tracking

Every schema and relation inspected in DERA carries immutable lineage telemetry detailing how, when, and by what engine version the metadata was extracted.

### Provenance Attributes

- **Source Engine**: Database technology (e.g. `postgresql`, `supabase`, `mysql`, `mariadb`, `sqlite`).
- **Server Version**: Upstream database version string reported during connector handshake.
- **Connector Adapter Version**: Semantic version of the DERA connector package executing the query.
- **Inspection Timestamp**: ISO 8601 UTC timestamp of the completed extraction.
- **Connection Identity**: Unique identifier of the connection used to extract the metadata.

```text
+--------------------------------------------------------------------------+
| Provenance Details                                                       |
| Source Engine: PostgreSQL 16.2 (Debian 16.2-1.pgdg120+1)                |
| Connector: dera-connector-postgres v1.4.0                                |
| Extracted At: 2026-10-31T14:15:00Z                                       |
| Connection ID: conn_7f1c9a4e                                             |
+--------------------------------------------------------------------------+
```
