"""DERA Diagnostics — Typed Rule Protocol.

Defines the structural typing contract adhered to by all diagnostic rules.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext
    from dera.diagnostics.models import RuleEvaluation, RuleMetadata


@runtime_checkable
class DiagnosticRule(Protocol):
    """Protocol satisfied by all deterministic diagnostic rule implementations."""

    @property
    def metadata(self) -> RuleMetadata:
        """Declared immutable metadata for the diagnostic rule."""
        ...

    def evaluate(self, context: DiagnosticContext) -> RuleEvaluation:
        """Evaluates the rule against the immutable diagnostic context.

        Returns a RuleEvaluation recording execution status, findings,
        timing, and error details if any.
        """
        ...
