"""DERA Diagnostics — Deterministic Rule Registry.

Provides thread-safe registration, inspection, and filtering of diagnostic rules,
preventing duplicate identifiers and preserving deterministic ordering.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from dera.diagnostics.enums import RuleCategory
from dera.diagnostics.exceptions import (
    DuplicateRuleError,
    InvalidRuleMetadataError,
    RuleNotFoundError,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from dera.diagnostics.protocols import DiagnosticRule

# Standard rule ID pattern: DERA-<CATEGORY>-<NUMBER> or RULE-<CATEGORY>-<NUMBER>
RULE_ID_PATTERN = re.compile(r"^[A-Z0-9]+(-[A-Z0-9]+)+$")


class DiagnosticRuleRegistry:
    """Registry managing the catalog of validated diagnostic rules."""

    def __init__(self) -> None:
        self._rules: dict[str, DiagnosticRule] = {}

    def register(self, rule: DiagnosticRule) -> None:
        """Registers a diagnostic rule.

        Raises:
            InvalidRuleMetadataError: If rule metadata is missing or malformed.
            DuplicateRuleError: If a rule with the same rule_id is already registered.
        """
        if not hasattr(rule, "metadata"):
            raise InvalidRuleMetadataError(
                "<unknown>", "Rule does not declare a metadata property."
            )

        meta = rule.metadata
        if not meta or not meta.rule_id:
            raise InvalidRuleMetadataError("<unknown>", "Rule declares empty or invalid rule_id.")

        if not RULE_ID_PATTERN.match(meta.rule_id):
            raise InvalidRuleMetadataError(
                meta.rule_id,
                f"Rule ID '{meta.rule_id}' does not match standard pattern (e.g. 'DERA-SCHEMA-001').",
            )

        if meta.rule_id in self._rules:
            existing = self._rules[meta.rule_id]
            raise DuplicateRuleError(
                rule_id=meta.rule_id,
                existing_version=existing.metadata.version,
                attempted_version=meta.version,
            )

        self._rules[meta.rule_id] = rule

    def register_many(self, rules: Iterable[DiagnosticRule]) -> None:
        """Registers multiple rules in deterministic order."""
        for rule in rules:
            self.register(rule)

    def get(self, rule_id: str) -> DiagnosticRule:
        """Retrieves a rule by its unique identifier.

        Raises:
            RuleNotFoundError: If no rule with rule_id exists.
        """
        if rule_id not in self._rules:
            raise RuleNotFoundError(rule_id)
        return self._rules[rule_id]

    def has(self, rule_id: str) -> bool:
        """Checks if a rule is registered."""
        return rule_id in self._rules

    def list_rules(self) -> list[DiagnosticRule]:
        """Returns all registered rules sorted deterministically by rule_id."""
        return sorted(self._rules.values(), key=lambda r: r.metadata.rule_id)

    def filter_rules(
        self,
        engine: str | None = None,
        category: RuleCategory | None = None,
        enabled_ids: set[str] | frozenset[str] | None = None,
        disabled_ids: set[str] | frozenset[str] | None = None,
    ) -> list[DiagnosticRule]:
        """Filters registered rules deterministically according to criteria."""
        results: list[DiagnosticRule] = []

        for rule in self.list_rules():
            meta = rule.metadata

            # Check explicit disabled list
            if disabled_ids and meta.rule_id in disabled_ids:
                continue

            # Check explicit enabled list
            if enabled_ids is not None and meta.rule_id not in enabled_ids:
                continue

            # Check category
            if category is not None and meta.category != category:
                continue

            # Check engine compatibility
            if engine is not None and meta.supported_engines:
                supported_norm = {e.lower() for e in meta.supported_engines}
                if engine.lower() not in supported_norm:
                    continue

            results.append(rule)

        return results

    def clear(self) -> None:
        """Removes all rules from the registry."""
        self._rules.clear()

    def __len__(self) -> int:
        return len(self._rules)

    def __contains__(self, rule_id: str) -> bool:
        return rule_id in self._rules
