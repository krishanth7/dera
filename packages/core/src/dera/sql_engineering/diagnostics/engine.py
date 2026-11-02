"""One bounded parse, deterministic rules, verified snapshot provenance and stable reports."""

from hashlib import sha256

from dera.reverse_engineering.snapshots.integrity import verify_snapshot_integrity
from dera.reverse_engineering.snapshots.models import SchemaSnapshot
from dera.sql_engineering.analyzer import analyze_with_ast
from dera.sql_engineering.models import Dialect

from .complexity import score
from .fingerprints import fingerprint
from .models import Finding, RuleEvaluation, SqlDiagnosticsReport
from .recommendations import recommend
from .registry import DIALECTS, REGISTRY
from .rules import schema, structural


class SqlDiagnosticsEngine:
    def analyze(
        self,
        sql: str,
        dialect: Dialect,
        schema_snapshot: SchemaSnapshot | None = None,
        *,
        include_complexity: bool = True,
        include_recommendations: bool = True,
    ) -> SqlDiagnosticsReport:
        snapshot = schema_snapshot
        if snapshot:
            if snapshot.engine != dialect:
                raise ValueError("Snapshot dialect mismatch")
            if (
                len(snapshot.payload.tables) > 1000
                or sum(len(t.columns) for t in snapshot.payload.tables) > 20000
            ):
                raise ValueError("Snapshot analysis resource limit exceeded")
            if not verify_snapshot_integrity(snapshot).is_valid:
                raise ValueError("Snapshot integrity verification failed")
        analysis, trees = analyze_with_ast(sql, dialect)
        findings = []
        skipped = {}
        query_hash = sha256(sql.encode("utf-8", errors="surrogatepass")).hexdigest()
        for index, tree in enumerate(trees):
            facts = structural.evaluate(tree)
            schema_facts, schema_skipped = schema.evaluate(tree, snapshot, dialect)
            facts.update(schema_facts)
            skipped.update(schema_skipped)
            for rule_id, evidence in sorted(facts.items()):
                rule = REGISTRY.get(rule_id)
                fid = fingerprint(
                    {
                        "query": query_hash,
                        "dialect": dialect,
                        "snapshot": snapshot.fingerprint if snapshot else None,
                        "statement": index,
                        "rule": rule_id,
                        "evidence": evidence,
                        "rules_version": "1.0.0",
                    }
                )
                findings.append(
                    Finding(
                        finding_id="sql_" + fid[:24],
                        rule_id=rule_id,
                        name=rule.name,
                        category=rule.category,
                        severity=rule.severity,
                        description=rule.description,
                        statement_index=index,
                        evidence=evidence,
                        confidence="SCHEMA_FACT" if rule.schema_required else "STRUCTURAL_FACT",
                        limitations=(
                            "Static observation only; server version, statistics, data distribution and measured cost are unavailable.",
                            "Source location is unavailable for this aggregate rule finding.",
                        ),
                        applicable_dialects=DIALECTS,
                    )
                )
        for diagnostic in analysis.diagnostics:
            if diagnostic.code == "unsafe_construct":
                continue
            rule_id = "SQL014" if diagnostic.code.startswith("dialect_feature:") else "SQL020"
            rule = REGISTRY.get(rule_id)
            findings.append(
                Finding(
                    finding_id="sql_"
                    + fingerprint(
                        {
                            "query": query_hash,
                            "dialect": dialect,
                            "rule": rule_id,
                            "code": diagnostic.code,
                        }
                    )[:24],
                    rule_id=rule_id,
                    name=rule.name,
                    category=rule.category,
                    severity=rule.severity,
                    description=rule.description,
                    statement_index=-1,
                    evidence=(diagnostic.code,),
                    location=diagnostic.span,
                    confidence="STRUCTURAL_FACT",
                    limitations=("Whole-input source span; no token-level accuracy claimed.",),
                    applicable_dialects=DIALECTS,
                )
            )
        findings.sort(key=lambda f: (f.rule_id, f.statement_index, f.finding_id))
        evaluations = tuple(
            RuleEvaluation(
                rule_id=r.rule_id,
                status="NOT_EVALUATED" if not trees or r.rule_id in skipped else "EVALUATED",
                reason="No validated AST available." if not trees else skipped.get(r.rule_id),
            )
            for r in REGISTRY.rules
        )
        indeterminate_codes = set(analysis.unsupported_constructs) - {"function_effects_unverified"}
        data = dict(
            analysis_status="INDETERMINATE"
            if not trees
            else "PARTIAL"
            if indeterminate_codes or skipped
            else "COMPLETE",
            dialect=dialect,
            analysis=analysis,
            complexity=score(trees) if trees and include_complexity else None,
            findings=tuple(findings),
            recommendations=tuple(recommend(f, REGISTRY.get(f.rule_id)) for f in findings)
            if include_recommendations
            else (),
            rule_evaluations=evaluations,
            total_findings=len(findings),
            snapshot_fingerprint=snapshot.fingerprint if snapshot else None,
            rules_version="1.0.0",
            report_version="1.0.0",
        )
        # Include options and input identity even if no findings or complexity are requested.
        payload = SqlDiagnosticsReport(**data, fingerprint="").model_dump(
            mode="json", exclude={"fingerprint"}
        )
        digest = fingerprint(
            {
                "input": query_hash,
                "options": [include_complexity, include_recommendations],
                "report": payload,
            }
        )
        return SqlDiagnosticsReport(**data, fingerprint=digest)
