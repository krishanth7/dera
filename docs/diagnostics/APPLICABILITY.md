# DERA Diagnostics — Rule Applicability Model

**Milestone:** Phase 8.1 — Deterministic Schema Diagnostic Rules Engine  
**Module:** `packages/core/src/dera/diagnostics/applicability.py`  
**Status:** Canonical Reference  

---

## 1. Overview

Before any diagnostic rule is executed, its declared prerequisites are matched against the runtime `DiagnosticContext`. This prevents misleading failure reports when an engine dialect lacks a feature or when inspection metadata is partial.

---

## 2. Applicability States

| Status | Meaning | Action Taken |
| :--- | :--- | :--- |
| `APPLICABLE` | All prerequisites (engine, capabilities, completeness) are satisfied. | Rule evaluates against context. |
| `NOT_APPLICABLE` | Rule scope does not match schema entities (e.g. partition rules on unpartitioned tables). | Skipped without penalty. |
| `UNSUPPORTED` | Database engine or connector dialect does not support the required feature (e.g. stored procedures in SQLite). | Recorded in coverage as unsupported; no false defects generated. |
| `INSUFFICIENT_METADATA` | Schema completeness is `PARTIAL` or `RESTRICTED`, preventing definitive verification. | Recorded in coverage as missing prerequisites rather than defects. |

---

## 3. Evaluation Flow

```python
def check_rule_applicability(
    rule: DiagnosticRule, context: DiagnosticContext
) -> tuple[ApplicabilityStatus, str]:
    # 1. Check supported_engines
    # 2. Check required_capabilities against SchemaCapabilityProfile
    # 3. Check metadata completeness level
```
