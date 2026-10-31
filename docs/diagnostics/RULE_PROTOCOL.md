# DERA Diagnostics — Rule Protocol

**Milestone:** Phase 8.1 — Deterministic Schema Diagnostic Rules Engine  
**Module:** `packages/core/src/dera/diagnostics/protocols.py`  
**Status:** Canonical Reference  

---

## 1. Specification

All DERA diagnostic rules implement the `DiagnosticRule` structural protocol:

```python
from typing import Protocol, runtime_checkable
from dera.diagnostics.context import DiagnosticContext
from dera.diagnostics.models import RuleEvaluation, RuleMetadata

@runtime_checkable
class DiagnosticRule(Protocol):
    """Protocol satisfied by all deterministic diagnostic rule implementations."""

    @property
    def metadata(self) -> RuleMetadata:
        """Declared immutable metadata for the diagnostic rule."""
        ...

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        """Evaluates the rule against the immutable diagnostic context.

        Returns a RuleEvaluation recording execution status, findings,
        timing, and error details if any.
        """
        ...
```

---

## 2. Implementation Invariants

1. **Pure Function Semantics:** The `evaluate` method must not mutate source databases, external files, or input context models.
2. **Deterministic Outputs:** Repeated execution of `evaluate` on identical contexts must produce identical `DiagnosticFinding` instances with stable fingerprints.
3. **No AI/LLM Calls:** Rule implementations must rely exclusively on deterministic static analysis algorithms.
4. **Structured Return:** Every execution must return a typed `RuleEvaluation` indicating `PASS`, `FINDINGS_DETECTED`, `NOT_APPLICABLE`, `UNSUPPORTED`, or `INSUFFICIENT_METADATA`.
