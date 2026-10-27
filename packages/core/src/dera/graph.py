"""Deterministic graph algorithms for database dependency resolution.

Builds Directed Acyclic Graphs (DAG) of foreign-key relationships,
detects circular dependencies, and computes topological sort orders.
"""

from __future__ import annotations

from collections.abc import Iterable

from dera.models import DatabaseTable


def build_dependency_graph(tables: Iterable[DatabaseTable]) -> dict[str, set[str]]:
    """Builds an adjacency list of table dependencies based on foreign keys.

    If Table A has a foreign key referencing Table B, edge B -> A is created
    so that B (the referenced prerequisite) precedes A in creation order.
    """
    graph: dict[str, set[str]] = {}
    table_map = {t.fully_qualified_name: t for t in tables}

    for fqn in table_map:
        graph[fqn] = set()

    for table in tables:
        src = table.fully_qualified_name
        for fk in table.foreign_keys:
            tgt = f"{fk.target_schema}.{fk.target_table}"
            if tgt in table_map and tgt != src:
                # tgt (referenced) must precede src (referencing)
                graph[tgt].add(src)

    return graph


def compute_topological_sort(tables: Iterable[DatabaseTable]) -> list[str]:
    """Computes a deterministic creation order for tables using Kahn's algorithm.

    Tables with zero dependencies are positioned first.
    Returns ordered list of fully-qualified table names.
    """
    table_list = list(tables)
    graph = build_dependency_graph(table_list)
    in_degree: dict[str, int] = {k: 0 for k in graph}

    for deps in graph.values():
        for dep in deps:
            in_degree[dep] += 1

    # Deterministic alphabetical ordering for nodes with same in-degree
    queue = sorted([node for node, deg in in_degree.items() if deg == 0])
    order: list[str] = []

    while queue:
        curr = queue.pop(0)
        order.append(curr)

        for neighbor in sorted(graph[curr]):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
                queue.sort()

    # If order doesn't include all tables, circular dependency exists; append remaining in order
    if len(order) < len(graph):
        remaining = sorted([n for n in graph if n not in order])
        order.extend(remaining)

    return order
