# Phase 10.1 SQL Engineering Architecture

## Baseline and specification

Inspected main commit `3419eaefd5ee790b35578a1dc25019f77102726c` on 2026-11-02.
No existing Phase 10.1 specification was found. The user brief governs this milestone.
The master roadmap contains stale Phase 1–9 status labels; this work does not certify those phases.
Phase 10 roadmap references transpilation and execution plans: both remain outside 10.1.
In particular, no EXPLAIN or EXPLAIN ANALYZE execution is introduced.

## Boundaries

The core package is `packages/core/src/dera/sql_engineering`:

- `dialects.py`: explicit grammar resolution.
- `analyzer.py`: bounded tokenization, strict parsing, AST inspection and diagnostics.
- `policy.py`: statement classification and conservative effect evaluation.
- `models.py`: strict typed results and canonical JSON serialization.

SQLGlot 30.27.0 is pinned to prevent unreviewed parser changes. Engine version includes
its installed version. No customer connector, worker, migration compiler or SQLAlchemy
execution path is imported into the analyzer. Phase 9 SQL compilation remains unchanged.
The existing connector query guards remain separate: these results never authorize execution.

## Capability matrix

| Dialect | Parser grammar | Explicit limits |
| --- | --- | --- |
| PostgreSQL | SQLGlot postgres | Grammar analysis, not server validation or function volatility resolution |
| SQLite | SQLGlot sqlite | MERGE, INTO, locking clauses and ILIKE flagged unsupported |
| MySQL | SQLGlot mysql | MERGE, ILIKE and RETURNING flagged unsupported |
| MariaDB | SQLGlot mysql common subset | MERGE and ILIKE flagged unsupported; no native MariaDB grammar |

Executable MySQL/MariaDB comments are rejected conservatively, including markers in literals.
Unknown parser commands and unsupported features never receive a read-only candidate result.
The matrix is a static analysis capability, not a guarantee that every accepted AST is valid
on every database server version. MariaDB-specific procedural syntax is not certified.

## Metadata and determinism

Objects and columns are syntactic SQL references; aliases and qualifiers are retained.
CTE names are excluded conservatively; global alias exclusion may omit unqualified objects
with the same name in another scope. No catalog identities, column lineage, inferred foreign
keys, wildcard expansion, types or function purity are invented. Joins and WHERE/HAVING
predicates are AST-rendered clauses, not inferred schema relationships. Parameters are
syntactic references, without bound values. Lists of references are sorted and deduplicated;
join and predicate traversal follows deterministic AST order.

Diagnostics use coarse whole-input spans, with zero-based Unicode code-point offsets and
exclusive ends. A rejected parse has statement_count zero: no partial statement count is claimed.
Safety is unsafe when effects are detected, unknown when analysis cannot establish a candidate,
or read_only_candidate for recognized query shapes. A candidate is never proof of safe execution:
views, custom operators, casts and database extensions can still have effects.
