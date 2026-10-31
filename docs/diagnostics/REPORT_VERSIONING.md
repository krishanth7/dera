# Report Versioning and Determinism Specification

## Overview

To support compliance verification and schema diff comparisons over time, DERA Phase 8.5 guarantees strict version tracking and deterministic report output.

## Subsystem Versions

Every diagnostic report captures the explicit versions of each underlying diagnostic subsystem:

- `engine_version`: Version of the core DERA diagnostic runner (`"8.5.0"`).
- `severity_policy_version`: Active severity derivation policy (`"1.0.0"`).
- `recommendation_catalog_version`: Active recommendation template catalog (`"1.0.0"`).
- `rule_versions`: Map of rule IDs to their semantic versions (e.g., `{"DERA-IDX-001": "1.0.0"}`).
- `configuration_fingerprint`: Cryptographic SHA-256 hash of all active configuration thresholds and rule parameters.

## Determinism Guarantees

1. **Byte-for-Byte Reproducibility**: Given identical input schema snapshots, connector capabilities, and configuration options, the diagnostic evaluator produces identical finding fingerprints, priority rankings, recommendations, and explainability summaries.
2. **Volatile Field Isolation**: Timestamps and execution durations are isolated in execution metadata and excluded from structural fingerprints and checksums.
3. **Sorted Serialization**: JSON reports are serialized with deterministic key sorting (`sort_keys=True`) and stable list orders.
