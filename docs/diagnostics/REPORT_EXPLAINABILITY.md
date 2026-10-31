# Report Explainability Specification

## Overview

DERA Phase 8.5 guarantees that every diagnostic report is fully explainable. An engineering lead or auditor inspecting a report must understand not only which issues were found, but also which rules ran, which were skipped, why findings were produced, what evidence supports each conclusion, and what metadata limitations remain.

## Explainability Summary Structure

Every canonical `DiagnosticReport` includes a `ReportExplainabilitySummary`:

```json
{
  "total_rules_registered": 15,
  "rules_evaluated": 15,
  "rules_skipped": 0,
  "rules_unsupported": 0,
  "insufficient_metadata_count": 0,
  "evaluation_errors_count": 0,
  "findings_by_severity": {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
    "INFORMATIONAL": 0
  },
  "findings_by_classification": {
    "CONFIRMED_STRUCTURAL_DEFECT": 1,
    "OPTIMIZATION_CANDIDATE": 2,
    "MAINTAINABILITY_CONCERN": 3
  },
  "total_suppressed_findings": 0,
  "evidence_completeness_breakdown": {
    "COMPLETE": 6,
    "PARTIAL": 0
  },
  "unresolved_reference_count": 0
}
```

## Explainability Guarantees

1. **Rule Accounting**: Every registered rule is accounted for. If a rule was skipped due to configuration or missing connector features, it is documented with an explicit reason.
2. **Metadata Transparency**: If a database engine or user role limits reflection (e.g., SQLite lack of check constraint reflection or PostgreSQL permission restriction), the summary highlights the affected rule count.
3. **Evidence Linkage**: Findings link directly to validated evidence records in the traceability matrix.
