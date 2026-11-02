"""Conservative AST safety policy. Never grants permission to execute SQL."""

from sqlglot import exp

MUTATIONS = {"Insert", "Update", "Delete", "Merge"}
DDL = {"Create", "Alter", "Drop", "TruncateTable"}
TRANSACTIONS = {"Transaction", "Commit", "Rollback"}
ADMIN = {"Grant", "Revoke", "Set", "Use", "Pragma", "Command", "Copy", "Execute", "Analyze"}


def classify(tree: exp.Expression) -> str:
    name = type(tree).__name__
    if name in MUTATIONS | DDL | TRANSACTIONS | ADMIN:
        return name.upper()
    if isinstance(tree, exp.Query):
        return "SELECT"
    return "UNKNOWN"


def evaluate(tree: exp.Expression) -> tuple[str, list[str]]:
    nodes = list(tree.walk())
    if any(
        type(n).__name__ in MUTATIONS | DDL | TRANSACTIONS | ADMIN | {"Into", "Lock", "PropertyEQ"}
        for n in nodes
    ):
        return "unsafe", (
            ["parser_command_fallback"] if any(isinstance(n, exp.Command) for n in nodes) else []
        )
    # Even apparently pure builtins can resolve to user-defined functions or operators.
    # No schema or trusted function-volatility catalog is available in this milestone.
    if any(isinstance(n, exp.Func) and not isinstance(n, exp.Exists) for n in nodes):
        return "unknown", ["function_effects_unverified"]
    if classify(tree) != "SELECT":
        return "unknown", ["unsupported_statement"]
    return "read_only_candidate", []
