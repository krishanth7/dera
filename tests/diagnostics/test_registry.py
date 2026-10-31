"""Tests for DERA diagnostic rule registry."""

from __future__ import annotations

import pytest
from dera.diagnostics.enums import DiagnosticSeverity, RuleCategory
from dera.diagnostics.exceptions import (
    DuplicateRuleError,
    InvalidRuleMetadataError,
    RuleNotFoundError,
)
from dera.diagnostics.models import RuleMetadata
from dera.diagnostics.registry import DiagnosticRuleRegistry


class DummyRule:
    """Mock rule implementation for testing registry functionality."""

    def __init__(
        self,
        rule_id: str,
        category: RuleCategory = RuleCategory.STRUCTURAL_INTEGRITY,
        supported_engines: tuple[str, ...] = (),
    ) -> None:
        self._metadata = RuleMetadata(
            rule_id=rule_id,
            title=f"Title for {rule_id}",
            description=f"Description for {rule_id}",
            version="1.0.0",
            category=category,
            default_severity=DiagnosticSeverity.MEDIUM,
            supported_object_kinds=("table",),
            supported_engines=supported_engines,
        )

    @property
    def metadata(self) -> RuleMetadata:
        return self._metadata

    def evaluate(self, context):  # noqa: ANN001, ANN201
        raise NotImplementedError


def test_registry_registration_and_lookup() -> None:
    registry = DiagnosticRuleRegistry()
    rule = DummyRule("DERA-TEST-001")

    assert not registry.has("DERA-TEST-001")
    registry.register(rule)
    assert registry.has("DERA-TEST-001")
    assert registry.get("DERA-TEST-001") is rule
    assert len(registry) == 1


def test_registry_duplicate_rejection() -> None:
    registry = DiagnosticRuleRegistry()
    rule1 = DummyRule("DERA-TEST-001")
    rule2 = DummyRule("DERA-TEST-001")

    registry.register(rule1)
    with pytest.raises(DuplicateRuleError) as exc_info:
        registry.register(rule2)

    assert exc_info.value.rule_id == "DERA-TEST-001"


def test_registry_invalid_metadata_rejection() -> None:
    registry = DiagnosticRuleRegistry()

    class BadRule:
        pass

    with pytest.raises(InvalidRuleMetadataError, match="declare a metadata property"):
        registry.register(BadRule())  # type: ignore[arg-type]


def test_registry_rule_not_found() -> None:
    registry = DiagnosticRuleRegistry()
    with pytest.raises(RuleNotFoundError):
        registry.get("DERA-NONEXISTENT-999")


def test_registry_deterministic_ordering_and_filtering() -> None:
    registry = DiagnosticRuleRegistry()
    rule_c = DummyRule("DERA-TEST-003", category=RuleCategory.RELATIONSHIPS)
    rule_a = DummyRule(
        "DERA-TEST-001", category=RuleCategory.INDEXES, supported_engines=("postgresql",)
    )
    rule_b = DummyRule(
        "DERA-TEST-002", category=RuleCategory.INDEXES, supported_engines=("sqlite",)
    )

    registry.register_many([rule_c, rule_a, rule_b])

    # Listing must always be sorted by rule_id
    listed_ids = [r.metadata.rule_id for r in registry.list_rules()]
    assert listed_ids == ["DERA-TEST-001", "DERA-TEST-002", "DERA-TEST-003"]

    # Category filter
    idx_rules = registry.filter_rules(category=RuleCategory.INDEXES)
    assert [r.metadata.rule_id for r in idx_rules] == ["DERA-TEST-001", "DERA-TEST-002"]

    # Engine filter
    pg_rules = registry.filter_rules(engine="postgresql")
    assert [r.metadata.rule_id for r in pg_rules] == ["DERA-TEST-001", "DERA-TEST-003"]

    # Enabled / disabled filter
    enabled = registry.filter_rules(enabled_ids={"DERA-TEST-002", "DERA-TEST-003"})
    assert [r.metadata.rule_id for r in enabled] == ["DERA-TEST-002", "DERA-TEST-003"]

    disabled = registry.filter_rules(disabled_ids={"DERA-TEST-001"})
    assert [r.metadata.rule_id for r in disabled] == ["DERA-TEST-002", "DERA-TEST-003"]
