# DERA Diagnostics — Report Format

**Milestone:** Phase 8.1 — Deterministic Schema Diagnostic Rules Engine  
**Module:** `packages/core/src/dera/diagnostics/models.py`, `packages/core/src/dera/diagnostics/serialization.py`  
**Status:** Canonical Reference  

---

## 1. Schema Structure

The canonical JSON serialization of a `DiagnosticReport` adheres to the following structure:

```json
{
  "evaluation_id": "eval_a1b2c3d4e5f6",
  "evaluated_at": "2026-10-31T12:00:00Z",
  "snapshot_id": "snap_1234567890abcdef",
  "rule_set_version": "1.0.0",
  "config_fingerprint": "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
  "report_hash": "2f7882437e86f7f15f7f706669d28e7c125ddd617e65129f821f4e7cda05e7e1",
  "source_engine": "postgresql",
  "summary": {
    "total_rules_evaluated": 5,
    "rules_passed": 4,
    "rules_with_findings": 1,
    "rules_skipped": 0,
    "rules_unsupported": 0,
    "rules_insufficient_metadata": 0,
    "rules_errored": 0,
    "total_findings": 1,
    "findings_by_severity": {
      "CRITICAL": 0,
      "HIGH": 1,
      "MEDIUM": 0,
      "LOW": 0,
      "INFORMATIONAL": 0
    }
  },
  "coverage": {
    "evaluated_rules": ["DERA-SCHEMA-001", "DERA-SCHEMA-002", "DERA-SCHEMA-003", "DERA-SCHEMA-004", "DERA-SCHEMA-005"],
    "skipped_rules": [],
    "unsupported_rules": [],
    "insufficient_metadata_rules": [],
    "errored_rules": []
  },
  "findings": [
    {
      "fingerprint": "c1f72d8a56bc91d8487e2f5b6d9e0f3174291845183819e6d42637996c56db32",
      "rule_id": "DERA-SCHEMA-001",
      "rule_version": "1.0.0",
      "object_id": "public.orders.fk_orders_user",
      "severity": "HIGH",
      "title": "Unresolved foreign key target for 'fk_orders_user'",
      "description": "Table 'orders' defines foreign key 'fk_orders_user' targeting 'users', but the target is missing or invalid in the canonical registry.",
      "evidence": [
        {
          "object_id": "public.orders.fk_orders_user",
          "field_name": "referenced_table_name",
          "observed_value": "users",
          "expected_value": "Resolvable in schema registry",
          "message": "Foreign key 'fk_orders_user' on table 'orders' references table 'users' which cannot be resolved (status: missing).",
          "provenance_reference": null,
          "context_data": {
            "foreign_key_name": "fk_orders_user",
            "resolution_status": "missing",
            "source_table": "orders"
          }
        }
      ],
      "severity_rationale": "Dangling foreign key relationships prevent reliable DAG topological sorting and indicate possible schema drift or orphaned constraints.",
      "recommendation": "Verify whether the referenced table 'users' was intentionally excluded from the inspection scope or represents an orphaned foreign key."
    }
  ],
  "rule_evaluations": [
    {
      "rule_id": "DERA-SCHEMA-001",
      "rule_version": "1.0.0",
      "status": "FINDINGS_DETECTED",
      "findings": [],
      "execution_duration_ms": 1.25,
      "message": "Detected 1 unresolved relationship targets.",
      "error_details": null
    }
  ]
}
```
