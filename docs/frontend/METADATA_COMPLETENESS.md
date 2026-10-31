# Metadata Completeness Specification

**Document Reference**: `docs/frontend/METADATA_COMPLETENESS.md`  
**Milestone**: Phase 7.3 — Database Connection & Schema Explorer UI  

---

## 1. Completeness Classification States

Database connectors may encounter permission boundaries, unsupported catalog views, or network timeouts. DERA explicitly categorizes and reports metadata completeness to prevent presenting partial schemas as authoritative.

### Taxonomy of States

| State | Badge Color | Definition | Guidance |
|---|---|---|---|
| `complete` | Green | Full catalog extraction succeeded; all relations and constraints captured | Schema is fully verified |
| `partial` | Yellow | Basic tables retrieved, but some constraint or index catalogs were inaccessible | Check database user privileges |
| `restricted` | Orange | Insufficient permissions on system metadata catalogs (e.g. `information_schema`) | Grant `SELECT` on system tables |
| `unknown` | Gray | Extraction completed without definitive completeness markers | Refresh inspection |

---

## 2. Honest Rendering Principle

The frontend strictly adheres to the principle of deterministic transparency: missing metadata is never presented as proof that an index or constraint does not exist. Uncaptured objects are flagged as uninspected.
