# Phase 6.4 Dependency Validation Engine

## 1. Overview

The dependency validation engine (`validate_dependency_analysis`) performs comprehensive verification of the computed analysis results against graph theory invariants and relational database constraints.

---

## 2. Validation Rules & Severities

| Rule Code | Severity | Description | Condition |
| :--- | :--- | :--- | :--- |
| `DEP_ORDERING_COMPLETENESS` | `ERROR` | Missing nodes in linear creation order for an acyclic schema. | `len(creation_order) != len(nodes)` on DAG. |
| `DEP_LEVEL_STRATIFICATION` | `ERROR` | Duplicate nodes across levels or incomplete level partition. | Union of level members $\neq$ set of nodes. |
| `DEP_UNBREAKABLE_CYCLE` | `ERROR` | Circular dependency with no viable breaking strategy. | Cycle contains no nullable or deferrable constraints. |
| `DEP_CYCLE_DETECTED` | `WARNING` | Circular dependency detected in schema. | Cycle is detected but has viable break strategies. |
| `DEP_CYCLE_TRUNCATED` | `WARNING` | Cycle enumeration reached configured bound. | `found_cycles >= max_cycles`. |

---

## 3. Strict Validation Mode

When calling `validate_dependency_analysis(result, mode=ValidationMode.STRICT)`, any finding with severity `ERROR` raises a `DependencyValidationError`, preventing corrupted or partial ordering plans from propagating to downstream migration engines. Under `mode=ValidationMode.PERMISSIVE` (default), all findings are returned as a tuple without raising exceptions.
