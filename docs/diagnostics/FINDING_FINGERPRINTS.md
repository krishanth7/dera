# Finding Fingerprints and Deduplication Specification

## Overview

DERA Phase 8.5 guarantees stable finding identity across repeated diagnostic evaluations. Because timestamps, random UUIDs, and volatile runtime metrics change between runs, DERA generates structural cryptographic fingerprints.

## Fingerprint Derivation

A finding fingerprint is a deterministic 64-character hex string computed using SHA-256 over canonical structural tokens:

```text
Fingerprint = SHA-256(rule_id:rule_version:canonical_object_id:sorted_evidence_keys_and_values)
```

### Components of the Fingerprint Payload

1. **`rule_id`**: The stable diagnostic rule code (e.g., `DERA-IDX-001`).
2. **`rule_version`**: Semantic version of the rule logic (e.g., `1.0.0`).
3. **`object_id`**: Fully qualified canonical object identifier (e.g., `public.orders`).
4. **`evidence_discriminator`**: Sorted key-value pairs of structural identifiers (such as column names, index names, or constraint names).

### Volatile Field Exclusion

The fingerprint calculation strictly excludes:
- Evaluation timestamps
- Temporary execution durations
- Internal memory addresses or UUIDv4 values
- Transient user session tokens

## Deduplication Guarantees

- **Exact Duplicate Collapse**: If multiple rules or execution passes produce findings with identical fingerprints on the same object, only one finding is retained in the canonical report.
- **Distinct Edge Integrity**: Findings relating to distinct foreign keys, indexes, or columns on the same table produce distinct fingerprints and are never collapsed into an ambiguous single finding.
