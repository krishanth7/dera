"""Structural observations, intentionally advisory rather than performance assertions."""

from collections import defaultdict

from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope

from ..complexity import depth


def evaluate(tree: exp.Expression) -> dict[str, tuple[str, ...]]:
    facts = defaultdict(list)

    def add(rule_id, fact):
        facts[rule_id].append(fact)

    nodes = list(tree.walk())
    for select in tree.find_all(exp.Select):
        if any(p.is_star for p in select.expressions):
            add("SQL001", "SELECT projection contains a wildcard (COUNT(*) is excluded).")
        if select.args.get("order") and not select.args.get("limit"):
            add("SQL011", "ORDER BY without LIMIT in the same SELECT.")
        if select.args.get("distinct"):
            add("SQL012", "DISTINCT is present.")
        group = select.args.get("group")
        if group and len(group.expressions) > 4:
            add("SQL013", f"GROUP BY expressions: {len(group.expressions)}.")
        if (
            select.args.get("from_")
            and not select.args.get("where")
            and not select.args.get("limit")
        ):
            add("SQL017", "Source SELECT has no WHERE and no LIMIT; output cardinality is unknown.")
        if select.args.get("limit") and not select.args.get("order"):
            add("SQL018", "LIMIT without ORDER BY in the same SELECT.")
    for node in nodes:
        if isinstance(node, (exp.Update, exp.Delete)) and not node.args.get("where"):
            add("SQL002", f"{type(node).__name__.upper()} has no WHERE clause.")
        if isinstance(node, exp.Join) and not node.args.get("on") and not node.args.get("using"):
            if node.args.get("kind") == "CROSS":
                add("SQL004", "Explicit CROSS JOIN.")
            elif not any(node.args.get(key) for key in ("kind", "side", "method")):
                add("SQL003", "Conditionless join with no explicit kind.")
        if (
            isinstance(node, (exp.Like, exp.ILike))
            and isinstance(node.expression, exp.Literal)
            and node.expression.is_string
            and not isinstance(node.parent, exp.Escape)
        ):
            if str(node.expression.this).startswith(("%", "_")):
                add("SQL006", "LIKE has a leading wildcard; the literal value is omitted.")
        if isinstance(node, (exp.Where, exp.Having)):
            if any(
                isinstance(f, exp.Func) and not isinstance(f, exp.Exists) and f.find(exp.Column)
                for f in node.walk()
            ):
                add("SQL005", "A predicate contains a function with a column argument.")
        if isinstance(node, exp.SetOperation) and node.args.get("distinct") is not False:
            add("SQL019", f"{type(node).__name__.upper()} requests duplicate elimination.")
    ors = sum(isinstance(n, exp.Or) for n in nodes)
    if ors >= 4:
        add("SQL007", f"OR node count: {ors}.")
    joins = sum(isinstance(n, exp.Join) for n in nodes)
    if joins >= 8:
        add("SQL010", f"Join node count: {joins}.")
    maximum = depth(tree)
    if maximum > 16:
        add("SQL009", f"Maximum AST depth: {maximum} (root depth zero).")
    for scope in traverse_scope(tree):
        if not scope.is_subquery:
            continue
        for column in scope.columns:
            if not column.table or column.table in scope.sources:
                continue
            parent = scope.parent
            while parent:
                if column.table in parent.sources:
                    add(
                        "SQL008",
                        "Qualified column resolves to an outer scope alias; unqualified correlations are not inferred.",
                    )
                    break
                parent = parent.parent
    return {k: tuple(sorted(set(v))) for k, v in facts.items()}
