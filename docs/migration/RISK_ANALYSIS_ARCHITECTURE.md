# DERA Migration Risk Analysis Architecture

**Phase:** 9.2 — Schema Change Classification & Migration Risk Analysis  
**Module:** `dera.migration`  
**Status:** Certified Read-Only, Deterministic  

---

## 1. Architectural Overview

The Migration Risk Analysis Engine consumes Phase 9.1 `ComparisonReport` records and Phase 6 `ForeignKeyGraph` dependency multigraphs to evaluate backward compatibility, potential data loss, operational locking caveats, and downstream dependency blast radius.

```mermaid
graph TD
    A[Phase 9.1 ComparisonReport] --> C[Change Classifier]
    G[Phase 6 ForeignKeyGraph] --> B[Dependency Blast Radius Analyzer]
    C --> Cls[Classified Changes]
    Cls --> Eval[Risk Evaluator]
    B --> Eval
    Eval --> Data[Data Preservation Risks]
    Eval --> Compat[Compatibility & Constraint Risks]
    Eval --> Locking[Operational & Availability Risks]
    Eval --> Blast[Dependency Impact Risks]
    Data --> Rec[Advisory Engineering Recommendations]
    Compat --> Rec
    Locking --> Rec
    Blast --> Rec
    Rec --> Pri[Review Priority Ordering: P1 -> P5]
    Pri --> Dig[SHA-256 Digest & Fingerprint]
    Dig --> Report[MigrationRiskReport]
```

## 2. Invariants & Guarantees

1. **Zero AI / LLM / Probabilistic Inference:** Rules are 100% deterministic, grounded strictly in schema metadata.
2. **Read-Only Operation:** Zero SQL execution, zero customer database mutations.
3. **Conservative Risk Assignment:** Potential data loss is flagged with `CONDITIONAL` certainty unless demonstrated by execution context.
4. **No Premature Migrations:** DDL/DML script generation is deferred to Phase 9.3+.
