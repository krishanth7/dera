# Maintainability Security & Guardrails

## Non-Negotiable Security Guarantees

Phase 8.4 maintainability diagnostics strictly enforce DERA core security invariants:

1. **Read-Only Operation**:
   Diagnostics operate exclusively on in-memory canonical schema representations, immutable snapshots, and dependency multigraphs. No SQL queries (`SELECT`, `SHOW`, `ALTER`, `DROP`) are executed against connected customer databases.
2. **Zero AI / LLM / ML Services**:
   Scoring, naming analysis, and metrics use 100% deterministic local Python logic, regular expressions, and graph traversals. No prompt tokens, customer schema names, or metadata are ever transmitted to external AI endpoints.
3. **Workspace Isolation**:
   Evaluations are strictly bound to the authenticated `workspace_id`. Diagnostic reports are isolated per tenant; cross-workspace metric aggregation is prevented.
4. **Credential and Secret Sanitization**:
   Identifier analysis strips database connection strings, passwords, and host credentials. Diagnostic findings and evidence contain only schema entity metadata.
5. **Resource Bounding & Limits**:
   Evaluation execution is bounded by `DiagnosticResourceLimits`:
   - `max_objects`: 100,000 entities ceiling.
   - `max_edges`: 100,000 relationship ceiling.
   - `max_findings`: 10,000 findings limit per report.
   - `timeout_seconds`: 60.0s execution timeout.
