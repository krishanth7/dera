"""Offline SQLGlot analysis with bounded input, tokens, nesting and AST size."""

import sqlglot
from sqlglot import exp
from sqlglot.errors import ErrorLevel, SqlglotError
from sqlglot.optimizer.scope import traverse_scope

from .dialects import resolve
from .models import Analysis, Diagnostic, Dialect, Span, Statement
from .policy import classify, evaluate

MAX_BYTES = 16_384
MAX_TOKENS = 2_048
MAX_DEPTH = 48
MAX_STATEMENTS = 32
ENGINE_VERSION = f"dera-sql/1.0.0+sqlglot/{sqlglot.__version__}"


def analyze(sql: str, dialect: Dialect) -> Analysis:
    """Analyze without retaining an AST in the public response."""
    return analyze_with_ast(sql, dialect)[0]


def analyze_with_ast(sql: str, dialect: Dialect) -> tuple[Analysis, tuple[exp.Expression, ...]]:
    """Share the validated, resource-bounded AST with offline engineering services.

    Parses once. Rejected inputs expose no partial AST. Callers must not mutate trees.
    """
    trees: list[exp.Expression] = []
    result = _analyze(sql, dialect, trees)
    return result, tuple(trees)


def _analyze(sql: str, dialect: Dialect, trees_out: list[exp.Expression]) -> Analysis:
    parser = resolve(dialect)
    span = Span(start=0, end=len(sql))

    def rejected(code: str, message: str) -> Analysis:
        return Analysis(
            dialect=dialect,
            engine_version=ENGINE_VERSION,
            statement_count=0,
            diagnostics=[Diagnostic(code=code, message=message, span=span)],
            unsupported_constructs=[code],
            safety="unknown",
        )

    try:
        byte_count = len(sql.encode("utf-8"))
    except UnicodeError:
        return rejected("invalid_input", "SQL contains invalid Unicode.")
    if byte_count > MAX_BYTES:
        return rejected("resource_limit", "SQL exceeds the UTF-8 byte limit.")
    if "\x00" in sql:
        return rejected("invalid_input", "Null bytes are unsupported.")
    # MySQL executable comments are not ordinary comments; never discard their effects.
    if "/*!" in sql or "/*M!" in sql:
        return rejected(
            "executable_comment", "Executable comments require engine-specific evaluation."
        )
    try:
        tokens = sqlglot.tokenize(sql, read=parser)
        if len(tokens) > MAX_TOKENS:
            return rejected("resource_limit", "SQL exceeds the token limit.")
        depth = 0
        for token in tokens:
            if token.token_type.name in {"L_PAREN", "L_BRACKET"}:
                depth += 1
                if depth > MAX_DEPTH:
                    return rejected("resource_limit", "SQL exceeds the nesting limit.")
            elif token.token_type.name in {"R_PAREN", "R_BRACKET"}:
                depth -= 1
        if sum(t.token_type.name == "SEMICOLON" for t in tokens) >= MAX_STATEMENTS:
            return rejected("resource_limit", "SQL exceeds the statement limit.")
        trees = [
            t
            for t in sqlglot.parse(
                sql, read=parser, error_level=ErrorLevel.RAISE, error_message_context=0
            )
            if t is not None and not isinstance(t, exp.Semicolon)
        ]
    except (SqlglotError, RecursionError, ValueError):
        # Do not echo parser exceptions: they contain raw SQL and potentially secrets.
        return rejected("parse_error", "SQL could not be analyzed under the selected grammar.")
    if not trees:
        return rejected("empty_input", "No SQL statements found.")
    statements = []
    unsupported = set()
    for tree in trees:
        nodes = list(tree.walk())
        if len(nodes) > 4_096:
            return rejected("resource_limit", "SQL exceeds the AST node limit.")
        # Reject deep expression chains before recursive SQL rendering.
        stack = [(tree, 0)]
        while stack:
            node, level = stack.pop()
            if level > MAX_DEPTH:
                return rejected("resource_limit", "SQL exceeds the AST depth limit.")
            stack.extend((child, level + 1) for child in node.iter_expressions())
        safety, reasons = evaluate(tree)
        unsupported_nodes = {
            "sqlite": {"Merge", "Into", "Lock", "ILike"},
            "mysql": {"Merge", "ILike", "Returning"},
            "mariadb": {"Merge", "ILike"},
            "postgresql": set(),
        }[dialect]
        features = sorted({type(n).__name__ for n in nodes} & unsupported_nodes)
        if features:
            reasons = reasons + ["dialect_feature:" + f for f in features]
            if safety != "unsafe":
                safety = "unknown"
        unsupported.update(reasons)
        # These are syntactic references, not resolved catalog identities. CTE aliases
        # are excluded from objects, but columns deliberately retain their SQL qualifiers.
        scopes = list(traverse_scope(tree))
        physical_tables = {
            id(source)
            for scope in scopes
            for source in scope.sources.values()
            if isinstance(source, exp.Table)
        }

        def render(n):
            return n.sql(dialect=parser)

        statements.append(
            Statement(
                statement_type=classify(tree),
                safety=safety,
                objects=sorted(
                    {
                        render(n)
                        for n in tree.find_all(exp.Table)
                        if not scopes or id(n) in physical_tables
                    }
                ),
                columns=sorted({render(n) for n in tree.find_all(exp.Column)}),
                joins=[render(n) for n in tree.find_all(exp.Join)],
                predicates=[render(n) for n in nodes if isinstance(n, (exp.Where, exp.Having))],
                parameters=sorted(
                    {render(n) for n in nodes if isinstance(n, (exp.Placeholder, exp.Parameter))}
                ),
            )
        )
    safety = (
        "unsafe"
        if any(s.safety == "unsafe" for s in statements)
        else ("unknown" if unsupported else "read_only_candidate")
    )
    diagnostics = [
        Diagnostic(code=r, message="Static analysis cannot establish execution safety.", span=span)
        for r in sorted(unsupported)
    ]
    if safety == "unsafe":
        diagnostics.append(
            Diagnostic(
                code="unsafe_construct",
                message="Mutation, control, administrative or locking construct detected.",
                span=span,
            )
        )
    trees_out.extend(trees)
    return Analysis(
        dialect=dialect,
        engine_version=ENGINE_VERSION,
        statement_count=len(statements),
        statements=statements,
        diagnostics=diagnostics,
        unsupported_constructs=sorted(unsupported),
        safety=safety,
    )
