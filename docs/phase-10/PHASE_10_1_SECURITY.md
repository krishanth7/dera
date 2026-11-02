# Phase 10.1 Security

## Trust boundaries

Only platform session authentication and authoritative workspace membership determine access.
The endpoint reuses `require_workspace_permission_by_id(Permission.SCHEMA_READ)` and
`verify_csrf`; user identity, workspace membership and role never come from the body.
No SQL is sent to a customer database. Platform DB reads for authentication and session
activity are distinct from customer SQL execution. Results have no shared cache or storage.

## Conservative evaluation

Every AST node is inspected, including data-modifying CTEs and nested subqueries.
DML, DDL, transactions, administration, SELECT INTO and locks are not candidates.
Unverified functions return unknown, including nextval, advisory locks, extension loading,
custom functions and MySQL locks. Executable comments and parser fallback commands are
unsupported. No safety label is an execution permission or proof of absence of effects.

## Resource and logging policy

Limits: 65,536 raw request bytes, 16,384 SQL UTF-8 bytes, 2,048 tokens,
48 lexical/AST nesting levels, fewer than 32 semicolons and at most 4,096 AST nodes.
These deterministic structural limits bound accepted work; they are not a wall-clock timeout
or an operating-system memory quota. Deployments must retain gateway concurrency/rate limits.
Parsing runs in FastAPI's synchronous endpoint worker pool rather than on the event loop.
Recursion errors during parsing become unknown. Parser exceptions are never reflected.
SQLGlot fallback logging has zero SQL context; the analyzer emits no SQL or credential logs.
Existing validation handlers omit raw input values.

## Residual limitations

SQLGlot grammars are broader than individual server versions. Static analysis has no trusted
schema snapshot, function volatility catalog or extension policy. Custom operators, views
and casts may have effects even when a query is a read_only_candidate. MariaDB uses only
the documented MySQL common subset. This module must never replace connector enforcement.
