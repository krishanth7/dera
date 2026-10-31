# DERA Diagnostics — Rule Registry

**Milestone:** Phase 8.1 — Deterministic Schema Diagnostic Rules Engine  
**Module:** `packages/core/src/dera/diagnostics/registry.py`  
**Status:** Canonical Reference  

---

## 1. Responsibilities

The `DiagnosticRuleRegistry` provides deterministic catalog management for all validated diagnostic rules.

### Core Capabilities
- **Registration & Validation:** Verifies rule metadata against structural constraints and standard ID formatting (`DERA-<CATEGORY>-<NUMBER>`).
- **Duplicate Prevention:** Immediately raises `DuplicateRuleError` if a rule with the same `rule_id` is registered.
- **Deterministic Listing:** Always returns rules sorted alphabetically by `rule_id`.
- **Criteria Filtering:** Supports filtering rules by database engine dialect, functional category, explicit enabled list, and explicit disabled list.

---

## 2. API Reference

```python
class DiagnosticRuleRegistry:
    def register(self, rule: DiagnosticRule) -> None: ...
    def register_many(self, rules: Iterable[DiagnosticRule]) -> None: ...
    def get(self, rule_id: str) -> DiagnosticRule: ...
    def has(self, rule_id: str) -> bool: ...
    def list_rules(self) -> list[DiagnosticRule]: ...
    def filter_rules(
        self,
        engine: str | None = None,
        category: RuleCategory | None = None,
        enabled_ids: set[str] | frozenset[str] | None = None,
        disabled_ids: set[str] | frozenset[str] | None = None,
    ) -> list[DiagnosticRule]: ...
```
