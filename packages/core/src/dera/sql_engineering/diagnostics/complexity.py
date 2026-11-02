"""Version 1 structural score, with explicit factors and no cost estimation."""

from collections.abc import Sequence

from sqlglot import exp

from .models import Complexity, ComplexityFactor

WEIGHTS = {
    "joins": 3,
    "nested_queries": 3,
    "ctes": 2,
    "max_ast_depth": 1,
    "predicate_nodes": 1,
    "aggregates": 2,
    "windows": 3,
    "set_operations": 3,
    "object_references": 1,
}


def depth(tree: exp.Expression) -> int:
    stack = [(tree, 0)]
    maximum = 0
    while stack:
        node, level = stack.pop()
        maximum = max(maximum, level)
        stack.extend((n, level + 1) for n in node.iter_expressions())
    return maximum


def score(trees: Sequence[exp.Expression]) -> Complexity:
    nodes = [n for tree in trees for n in tree.walk()]
    counts = {
        "joins": sum(isinstance(n, exp.Join) for n in nodes),
        "nested_queries": sum(isinstance(n, exp.Subquery) for n in nodes),
        "ctes": sum(isinstance(n, exp.CTE) for n in nodes),
        "max_ast_depth": max((depth(t) for t in trees), default=0),
        "predicate_nodes": sum(
            isinstance(n, (exp.Predicate, exp.And, exp.Or, exp.Not)) for n in nodes
        ),
        "aggregates": sum(isinstance(n, exp.AggFunc) for n in nodes),
        "windows": sum(isinstance(n, exp.Window) for n in nodes),
        "set_operations": sum(isinstance(n, exp.SetOperation) for n in nodes),
        "object_references": sum(isinstance(n, exp.Table) for n in nodes),
    }
    factors = tuple(
        ComplexityFactor(
            name=k, count=counts[k], weight=WEIGHTS[k], contribution=counts[k] * WEIGHTS[k]
        )
        for k in sorted(WEIGHTS)
    )
    total = sum(f.contribution for f in factors)
    return Complexity(
        score=total,
        band="LOW" if total < 25 else "MODERATE" if total < 60 else "HIGH",
        factor_breakdown=factors,
    )
