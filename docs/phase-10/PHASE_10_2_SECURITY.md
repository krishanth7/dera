# Phase 10.2 Security and Trust Boundaries

## No execution

The diagnostics engine consumes only resource-bounded ASTs and trusted immutable metadata.
It has no connector import, dynamic eval/exec, customer connection, SQL rewrite or mutation path.
The API's platform database access authenticates sessions and memberships only. Snapshot
retrieval uses existing storage; it never refreshes metadata from a customer database.

## Identity and snapshots

The existing session dependency validates the authoritative user/session and active workspace
membership with default-deny schema:read. Snapshot requests check snapshot:read, use the
workspace ID from the authorized workspace entity, then independently compare the returned
snapshot's workspace identity. Foreign and missing snapshots both return 404. Snapshots are
deep-copied before worker dispatch, verified cryptographically and checked for engine compatibility.
Client JSON cannot supply identity, roles, memberships, schema payloads or connection credentials.

## Bounded work and information handling

Existing Phase 10.1 limits remain: 65,536 raw request bytes, 16,384 SQL characters and UTF-8 bytes,
2,048 tokens, 48 lexical/AST depth, fewer than 32 semicolons and 4,096 AST nodes per statement.
Diagnostics add at most one aggregate finding per rule/statement plus baseline limitation findings.
Schema contexts are limited to 1,000 tables and 20,000 columns, alongside existing snapshot
integrity resource limits. These are structural limits, not OS memory quotas or wall-clock timeouts.
Gateway request/concurrency controls remain necessary for service-level DoS protection.

Parsing and diagnostics run in the worker thread pool; async authentication/storage runs in
the established FastAPI dependency layer. SQLGlot parser fallback logging remains zero-context;
parser exceptions and snapshot mismatch details are not reflected to clients. Diagnostics add
no SQL logs. Evidence omits predicate literal values, but the preserved baseline analysis may
contain rendered clauses and must not be logged by clients or proxies. Fingerprints are integrity
identifiers, not encryption or anonymization.

## Evidence limitations

No schema statistics, server collation/search path, data distribution, index usage or runtime
cost is inferred. Unknown function effects never become safe through diagnostics. A structural
complexity score is not a query execution estimate. Unsupported/indeterminate syntax stays
explicit. Recommendations always require manual review and do not authorize external execution.
