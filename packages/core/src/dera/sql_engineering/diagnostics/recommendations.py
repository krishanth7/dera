"""Deterministic advisory text; no SQL rewriting or invented performance promises."""

from .fingerprints import fingerprint
from .models import Finding, Recommendation
from .registry import Rule


def recommend(finding: Finding, rule: Rule) -> Recommendation:
    return Recommendation(
        recommendation_id="rec_"
        + fingerprint({"finding": finding.finding_id, "rule": rule.rule_id})[:24],
        finding_id=finding.finding_id,
        rule_id=rule.rule_id,
        title=rule.name,
        description=rule.description,
        evidence=finding.evidence,
        suggested_action=rule.action,
        expected_benefit="May improve clarity or validate intended semantics; any performance benefit requires workload measurements.",
        limitations=finding.limitations,
        manual_review_required=True,
    )
