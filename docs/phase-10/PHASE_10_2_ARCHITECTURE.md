# Phase 10.2 SQL Diagnostics Architecture

## Baseline and dependency

Verified 2026-11-02 through Cloud Browser repository navigation and the GitHub connection:
main is `3419eaefd5ee790b35578a1dc25019f77102726c`; PR #76 remains open, not merged.
The implementation branch `feat/phase-10-2-sql-diagnostics` explicitly depends on its
Phase 10.1 commit `d4492156f51bad318f997ea1ad86e2214613fb01`. No unmerged files were silently
copied to main. No repository Phase 10.2 specification was found; the supplied brief governs.
The user's opening instruction overrides the pasted PR workflow: upload through Cloud Browser,
without creating another pull request. Phase 10.1 is not merged by this work.

## Shared analysis pipeline

Phase 10.1 now exposes `analyze_with_ast`, returning its unchanged Analysis response and a tuple
of validated SQLGlot trees. The existing `analyze` API delegates to it. Rejected inputs expose
no partial AST. The diagnostics engine invokes this shared bounded parser exactly once.
ASTs are internal and never serialized, executed, or persisted by the diagnostics endpoint.

The new `diagnostics` package separates immutable models, a closed rule registry, structural
rules, scope-aware snapshot rules, complexity scoring, recommendations and fingerprinting.
The registry uses SQL001-style identifiers, separate from the Phase 8 schema-only registry's
hyphenated identifiers and schema context. It reuses Phase 8 DiagnosticSeverity rather than
creating a competing severity taxonomy. Phase 9 canonical serialization and domain-separated
SHA-256 provide stable report/finding/recommendation identity. Migration governance and risk
models were inspected but are not imported as SQL-query governance or approval mechanisms.

Findings are sorted by rule ID, statement index and finding ID. Evidence strings are deduplicated
and sorted. Recommendations are templates bound to their evidence; no generative model or SQL
rewrite exists. All rule severities are INFORMATIONAL except SQL002, which is HIGH.

## Schema context

Only immutable SchemaSnapshot payloads from existing snapshot storage are accepted by the API.
Workspace membership, schema:read, snapshot:read, workspace-keyed lookup, defense-in-depth
workspace identity comparison and cryptographic integrity checks precede schema diagnostics.
No client-supplied schema body, role, user identity or database connection is accepted.
The default existing reverse-engineering service uses process-local storage; multi-worker durable
snapshot availability remains a deployment concern outside this milestone.

Table and column resolution uses SQLGlot scopes for direct base tables. PostgreSQL unquoted
identifiers fold lower, quoted identifiers remain exact; SQLite identifiers compare case-insensitively.
MySQL/MariaDB columns compare case-insensitively; table case mismatches are indeterminate without
server settings. Unqualified names matching multiple namespaces are not guessed. Derived tables,
CTE output lineage, cross-catalog references, NATURAL/USING coalescence and projection alias
lineage are not inferred. Incomplete snapshots disable schema absence checks. Positive findings
may coexist with NOT_EVALUATED when other scopes cannot be resolved.

Index evidence is limited to recorded unconditional leading BTREE columns and primary-key
prefixes. Absence of this narrow evidence does not prove an unindexed query, a table scan,
or an index recommendation. Only single-column foreign-key equalities receive FK context;
missing/composite/incompatible join-key inference is deferred.

## Frontend and scope

No Phase 10.1 SQL editor or analysis UI exists in the inspected frontend, so none was replaced
or extended. This milestone supplies typed backend contracts for a later editor integration.
No transpilation, execution plans, automated rewrite, SQL execution or release is introduced.
