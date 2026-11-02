# Phase 10.3 Dialect Capabilities

| Dialect | Format token | Normalized estimates | Imported actuals | Limits |
|---|---|---|---|---|
| PostgreSQL | postgresql-json | Startup/total cost, rows, width | Average rows/time per invocation, loops; top-level execution time | One EXPLAIN object or one-element array; Plans child arrays |
| MySQL | mysql-json-v1 | Query-block query_cost, examined rows/scan, numeric/decimal-string filtered percent | Unavailable | Traditional query_block JSON; JSON v2 and TREE unsupported |
| MariaDB | mariadb-json | rows and filtered percent | r_rows average, r_loops, cumulative r_total_time_ms | Separate MariaDB wrapper and metric contracts; costs unavailable |
| SQLite | sqlite-eqp | Unavailable | Unavailable | JSON array of exact id/parent/notused/detail objects; VM bytecode rejected |

All workflows import external evidence. No format offers live acquisition. Canonical dialects
are `postgresql`, `mysql`, `mariadb`, `sqlite`; `postgres` is not an API dialect alias.

PostgreSQL operations include sequential/index/index-only/bitmap scans, nested/hash/merge joins,
sort/incremental sort, aggregates/window aggregates, materialization/memoization, gather/parallel,
CTE/recursive operations, append/set operations, result, limit and subquery wrappers. Unknown
Node Type values remain UNKNOWN and produce a PARTIAL report. Parallel worker properties are
retained without manufacturing additional execution children or adding worker measurements.

MySQL recognizes table access, nested_loop ordering, query blocks, ordering/grouping,
duplicate removal, materialized subqueries and union wrappers. `prefix_cost`, read/evaluation
costs and version-specific fields remain native metadata; no unsupported exclusive cost is inferred.
MariaDB separately recognizes filesort/read_sorted_file, temporary_table, block-nl-join,
materialized, expression_cache, subquery and union structures. Unrecognized nested metadata
produces explicit analysis limitations. EXPLAIN JSON does not constitute evidence that an index
is missing from the database catalog.

SQLite SCAN remains a full scan even when an index supplies order. SEARCH indicates indexed
access; a covering index is reported only when the description says so. Temporary B-tree,
materialization/co-routine and compound operations are recognized. Other descriptions remain
UNKNOWN. EQP textual details are version-sensitive; complex identifier/index descriptions may
remain native text without fully parsed identity. Node order and reported parent links are retained;
no synthetic join relationship is invented between sibling SQLite rows.

## Primary format references

- [PostgreSQL EXPLAIN semantics](https://www.postgresql.org/docs/current/using-explain.html)
- [MySQL EXPLAIN](https://dev.mysql.com/doc/refman/26.10/en/explain.html)
- [MariaDB EXPLAIN JSON](https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/analyze-and-explain-statements/explain-format-json)
- [MariaDB imported ANALYZE metrics](https://mariadb.com/docs/server/reference/sql-statements/administrative-sql-statements/analyze-and-explain-statements/analyze-format-json)
- [SQLite EQP structure and stability warning](https://www.sqlite.org/eqp.html)

These references informed interpretation; fixtures are controlled synthetic examples, not claimed
live captures or compatibility certification across every database version.
