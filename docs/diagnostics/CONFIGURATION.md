# DERA Diagnostics — Engine Configuration

**Milestone:** Phase 8.1 — Deterministic Schema Diagnostic Rules Engine  
**Module:** `packages/core/src/dera/diagnostics/context.py`  
**Status:** Canonical Reference  

---

## 1. DiagnosticEngineConfig

The evaluation configuration allows granular customization without mutating rule logic:

| Setting | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `enabled_rule_ids` | `frozenset[str] \| None` | `None` | If specified, only evaluate this subset of registered rules. |
| `disabled_rule_ids` | `frozenset[str]` | `frozenset()` | Suppress evaluation of specific rule IDs. |
| `included_categories` | `frozenset[RuleCategory] \| None` | `None` | Restrict evaluation to specific categories. |
| `excluded_categories` | `frozenset[RuleCategory]` | `frozenset()` | Exclude specific categories from evaluation. |
| `rule_thresholds` | `dict[str, Any]` | `{}` | Rule-specific tuning parameters (e.g. index column count limits). |
| `limits` | `DiagnosticResourceLimits` | Default limits | Resource ceilings guarding against denial-of-service. |

---

## 2. Resource Limits

`DiagnosticResourceLimits` bounds execution parameters:
- `max_objects`: Default `100_000` objects.
- `max_edges`: Default `100_000` relationship edges.
- `max_findings`: Default `10_000` aggregated findings.
- `timeout_seconds`: Default `60.0` seconds execution limit.
