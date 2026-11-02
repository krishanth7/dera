# Phase 10.2 SQL Rule Catalog

Rules version: `1.0.0`. Ordering: rule ID, statement index, finding ID. All dialects share
these conservative structural rules; parser capability limits remain explicit. Each rule emits
at most one aggregate finding per statement. Evidence is sorted and deduplicated.

| ID | Name | Severity | Evidence trigger / observation | Suggested action |
| --- | --- | --- | --- | --- |
| SQL001 | SELECT_STAR | INFORMATIONAL | Wildcard projection detected. | Consider explicit columns when the result contract is fixed. |
| SQL002 | MISSING_WHERE_ON_MUTATION | HIGH | UPDATE or DELETE has no WHERE clause. | Verify the intended affected rows before any external execution. |
| SQL003 | IMPLICIT_CROSS_JOIN | INFORMATIONAL | A join has no explicit condition or join kind. | Review the intended relationship and add an explicit condition when appropriate. |
| SQL004 | POSSIBLE_CARTESIAN_JOIN | INFORMATIONAL | Explicit CROSS JOIN produces row combinations. | Confirm that a Cartesian product is intentional. |
| SQL005 | NON_SARGABLE_PREDICATE | INFORMATIONAL | A predicate applies a function to a column. | Review expression-index coverage and semantics before changing the predicate. |
| SQL006 | LEADING_WILDCARD_LIKE | INFORMATIONAL | A LIKE pattern begins with a wildcard. | Review pattern semantics and engine-specific search indexes. |
| SQL007 | OR_PREDICATE_COMPLEXITY | INFORMATIONAL | At least four OR nodes occur in this statement. | Review predicate grouping and readability; preserve NULL and duplicate semantics. |
| SQL008 | CORRELATED_SUBQUERY | INFORMATIONAL | A nested scope refers to an outer-scope column. | Review the correlation with the schema; do not assume a join rewrite is equivalent. |
| SQL009 | EXCESSIVE_NESTING | INFORMATIONAL | AST depth exceeds 16 levels. | Consider separating logical stages for readability. |
| SQL010 | EXCESSIVE_JOIN_COUNT | INFORMATIONAL | At least eight joins occur in this statement. | Review join intent, cardinality assumptions and maintainability. |
| SQL011 | ORDER_BY_WITHOUT_LIMIT | INFORMATIONAL | An ORDER BY has no LIMIT in the same SELECT. | Confirm that ordering the full result is required; no limit is automatically recommended. |
| SQL012 | DISTINCT_USAGE_REVIEW | INFORMATIONAL | DISTINCT requests duplicate elimination. | Confirm duplicate semantics and avoid hiding unintended join multiplicity. |
| SQL013 | GROUP_BY_COMPLEXITY | INFORMATIONAL | A GROUP BY has more than four expressions. | Review grouping semantics and the intended output grain. |
| SQL014 | UNSUPPORTED_DIALECT_CONSTRUCT | INFORMATIONAL | The baseline identifies unsupported dialect syntax. | Use syntax supported by the selected grammar and server version. |
| SQL015 | AMBIGUOUS_COLUMN_REFERENCE | INFORMATIONAL | An unqualified column has multiple base-table candidates. | Qualify the column using the intended table alias. |
| SQL016 | TYPE_COMPATIBILITY_REVIEW | INFORMATIONAL | A simple column equality compares different known canonical types. | Review native types and conversion semantics before changing SQL. |
| SQL017 | UNBOUNDED_RESULT_POTENTIAL | INFORMATIONAL | A SELECT over a source has neither WHERE nor LIMIT. | Confirm the caller's result-volume contract; aggregates can still return few rows. |
| SQL018 | NONDETERMINISTIC_ORDERING | INFORMATIONAL | A SELECT has LIMIT without ORDER BY. | If stable paging is required, specify ordering with a verified unique tie-breaker. |
| SQL019 | EXPENSIVE_SET_OPERATION_PATTERN | INFORMATIONAL | A set operation requests duplicate elimination. | Use ALL only if retaining duplicates preserves the intended result. |
| SQL020 | PARSER_OR_ANALYSIS_LIMITATION | INFORMATIONAL | The baseline reports an analysis limitation. | Review the reported capability or input limit before relying on the analysis. |
| SQL101 | UNKNOWN_TABLE | INFORMATIONAL | A base table is absent from a complete snapshot. | Check the selected snapshot, schema qualification and table spelling. |
| SQL102 | UNKNOWN_COLUMN | INFORMATIONAL | A column is absent from resolved base tables in a complete snapshot. | Check aliases, spelling and snapshot freshness. |
| SQL103 | JOIN_INDEX_COVERAGE_REVIEW | INFORMATIONAL | No unconditional leading BTREE index is recorded for a join column. | Review existing index definitions, workload and write cost before proposing any index. |
| SQL104 | FILTER_INDEX_COVERAGE_REVIEW | INFORMATIONAL | No unconditional leading BTREE index is recorded for a filter column. | Review selectivity and existing indexes with a DBA before proposing any index. |
| SQL105 | FOREIGN_KEY_CONTEXT | INFORMATIONAL | A single-column join equality matches a recorded foreign key. | Use the recorded relationship as context; still review join direction and multiplicity. |
| SQL106 | IDENTIFIER_CASE_REVIEW | INFORMATIONAL | Identifier case semantics cannot be established for this reference. | Review server case settings and exact snapshot spelling. |

## Applicability and limitations

SQL015, SQL016 and SQL101–SQL106 require an authorized, integrity-verified immutable snapshot.
Without it, each returns NOT_EVALUATED, never a fabricated pass. Incomplete metadata disables
absence checks. SQL101/SQL102 inspect complete direct base-table scopes; derived or uncertain
sources are excluded from column inference. SQL016 reports different known canonical types,
not a verified implicit conversion or incompatibility. SQL106 reports MySQL-family case uncertainty.
SQL103/104 describe absent narrow BTREE-prefix evidence, not proven absence of every usable index.
SQL105 reports only single-column recorded FK matches; absence of an FK does not create a warning.

SQL001 excludes COUNT(*). SQL003 reports conditionless joins, including comma joins, but does not
infer a missing relationship. SQL004 identifies explicit CROSS JOIN semantics without claiming it
is erroneous. SQL005 is a function-on-column observation, not proof of non-sargability; expression
indexes may apply. SQL006 skips explicit ESCAPE clauses rather than guessing escape semantics.
SQL008 only recognizes qualified outer-scope alias references; unqualified correlation is deferred.
SQL011 is informational: ordering a full result can be correct. SQL017 states unbounded-result
potential; aggregate queries can still return few rows. SQL018 does not claim ordering uniqueness.
SQL019 requests semantic review of deduplication, never an unconditional UNION ALL rewrite.

Evidence confidence distinguishes STRUCTURAL_FACT from SCHEMA_FACT. Possible performance benefits
are always qualified in recommendations and require measurements. Recommendations contain stable
IDs, linked rule/finding IDs, description, evidence, suggested action, expected benefit, limitations
and manual_review_required=true. No rule emits an automatic SQL patch.
