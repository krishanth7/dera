# Evidence Validation Specification

## Overview

DERA Phase 8.5 introduces rigorous evidence validation before any finding is accepted into a diagnostic report. The validation layer guarantees that evidence references exist, values are sanitized, and sensitive credentials or private data are never leaked.

## Validation Protocol

Each evidence item undergoes systematic checks in `validate_and_enrich_evidence`:

1. **Object Existence Verification**: The referenced object ID is resolved against the `DatabaseSchema` snapshot. If the object cannot be located, the evidence is tagged as `unresolved`.
2. **Type Compatibility**: The declared `DiagnosticEvidenceType` must match the payload structure.
3. **Data Sanitization and Secret Minimization**:
   - Evidence values are scanned for sensitive keys (`password`, `secret`, `token`, `key`, `conn_str`).
   - String values matching credential patterns are redacted (`[REDACTED]`).
   - Customer table row data is never captured in diagnostic evidence; only structural metadata is permitted.
4. **Serialization Safety**: Evidence values are converted into deterministic JSON-serializable primitives (integers, strings, booleans, or sorted lists). Non-serializable objects (e.g., custom Python classes or memory pointers) are rejected or normalized.
5. **Completeness Assessment**: Evidence completeness is classified as `COMPLETE`, `PARTIAL`, `RESTRICTED`, `UNSUPPORTED`, or `UNKNOWN`.
