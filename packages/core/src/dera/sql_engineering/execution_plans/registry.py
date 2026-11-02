"""Explicit format and operation capabilities; no live acquisition capability."""

from types import MappingProxyType

CAPABILITIES = MappingProxyType(
    {
        "postgresql": ("postgresql-json", "estimated and imported actual metrics"),
        "mysql": ("mysql-json-v1", "estimated metrics; JSON v2 is unsupported"),
        "mariadb": ("mariadb-json", "estimated scan rows and imported r_* metrics"),
        "sqlite": ("sqlite-eqp", "normalized EQP rows; no costs or actual metrics"),
    }
)
PG_OPERATIONS = MappingProxyType(
    {
        "Seq Scan": "SCAN",
        "Index Scan": "INDEX_SCAN",
        "Index Only Scan": "INDEX_SCAN",
        "Bitmap Heap Scan": "BITMAP_SCAN",
        "Bitmap Index Scan": "BITMAP_SCAN",
        "Nested Loop": "NESTED_LOOP",
        "Hash Join": "HASH_JOIN",
        "Merge Join": "MERGE_JOIN",
        "Sort": "SORT",
        "Incremental Sort": "SORT",
        "Aggregate": "AGGREGATE",
        "Group": "AGGREGATE",
        "Materialize": "MATERIALIZE",
        "Memoize": "MATERIALIZE",
        "Gather": "PARALLEL",
        "Gather Merge": "PARALLEL",
        "CTE Scan": "CTE",
        "WorkTable Scan": "CTE",
        "Recursive Union": "CTE",
        "Append": "SET",
        "Merge Append": "SET",
        "SetOp": "SET",
        "Unique": "AGGREGATE",
        "Hash": "QUERY",
        "Limit": "QUERY",
        "Result": "QUERY",
        "Subquery Scan": "QUERY",
        "WindowAgg": "AGGREGATE",
        "BitmapAnd": "BITMAP_SCAN",
        "BitmapOr": "BITMAP_SCAN",
    }
)
MYSQL_CHILDREN = frozenset(
    {
        "query_block",
        "nested_loop",
        "table",
        "ordering_operation",
        "grouping_operation",
        "duplicates_removal",
        "materialized_from_subquery",
        "union_result",
        "query_specifications",
        "attached_subqueries",
        "optimized_away_subqueries",
        "buffer_result",
        "windowing",
        "windows",
    }
)
MARIADB_CHILDREN = frozenset(
    {
        "query_block",
        "nested_loop",
        "table",
        "read_sorted_file",
        "filesort",
        "temporary_table",
        "block-nl-join",
        "materialized",
        "subqueries",
        "expression_cache",
        "union_result",
        "query_specifications",
        "recursive_union",
    }
)
