# DERA Shared Contracts Documentation Index

> **Package:** `packages/contracts`  
> **Maintainer:** Krishanth  
> **Status:** Active Documentation Hub  
> **Last Verified:** 2026-10-26 (Commit `e550fdd`)  

---

## 1. Contracts Specifications Index

| Document | Purpose | Status |
|---|---|---|
| [**SCHEMA_CONTRACTS.md**](SCHEMA_CONTRACTS.md) | JSON Schema exchange definitions, TypeScript interfaces, and Python dataclass field correspondence | **Active** |

---

## 2. Key Contract Invariants

1. **Protocol Parity:** Shared interfaces guarantee identical data structures between backend introspection services and frontend web studios.
2. **Zero Runtime Dependencies:** `packages/contracts` has zero external runtime npm dependencies.
3. **Draft 2020-12 JSON Schema:** Canonical exchange schemas follow modern JSON Schema standards.
4. **Deterministic Serializability:** Contracts are designed for canonical sorting and cryptographic hashing.

---

## 3. Related Documentation Hubs

- [Root Documentation Hub](../README.md)
- [System Architecture Overview](../architecture/SYSTEM_OVERVIEW.md)
- [Core Domain Models](../core/README.md)
- [Backend API Contracts](../backend/API_CONTRACTS.md)
- [Frontend Architecture](../frontend/APPLICATION_ARCHITECTURE.md)
