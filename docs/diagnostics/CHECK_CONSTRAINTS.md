# DERA-CON-004: Check Constraint Metadata Integrity

## 1. Specification
Rule `DERA-CON-004` verifies the metadata completeness of table CHECK constraints without executing SQL expressions.

## 2. Security & Passive Inspection
- **Untrusted SQL Text**: Check expressions extracted from database catalogs are treated strictly as untrusted data. DERA NEVER evaluates, compiles, or executes check expressions against any database engine.
- **XSS & Output Sanitization**: Check clauses are sanitized and escaped prior to inclusion in diagnostic reports or API payloads.
- **Empty Check Clause Detection**: Detects declared CHECK constraints where the extracted clause is empty or whitespace-only (`DiagnosticSeverity.HIGH`).
- **Engine Applicability**: Validates that the underlying database engine supports CHECK constraint enforcement before evaluating the rule.
