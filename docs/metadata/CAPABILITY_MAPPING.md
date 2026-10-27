# Capability-Aware Normalization

**Subsystem:** `dera.metadata.capabilities`  

---

## 1. Metadata Completeness States

1. **`COMPLETE`**: Engine actively supports and fully catalogs the feature.
2. **`PARTIAL`**: Engine catalogs the feature with structural omissions (e.g. SQLite unnamed check constraints or expression indexes).
3. **`RESTRICTED`**: Engine catalog exists, but the connected database role lacks permission to inspect the object (e.g. `SHOW VIEW` denied in MySQL).
4. **`UNSUPPORTED`**: Engine or server version does not implement the feature (e.g. stored procedures in SQLite, check constraints in MySQL < 8.0.16).
5. **`UNKNOWN`**: Inspection could not determine completeness with high confidence.

---

## 2. Integration with Phase 5.1 Capability Model

The normalizer accepts `capabilities: dict[str, Any]` derived from Phase 5 connector capability probes to dynamically annotate provenance records and prevent false assumptions about missing schema elements.
