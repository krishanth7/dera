"""DERA Diagnostics — Domain Exception Hierarchy.

Defines typed errors for rule registration, execution, resource bounding,
and validation failures in the diagnostic engine.
"""

from __future__ import annotations


class DiagnosticEngineError(Exception):
    """Base exception for all DERA diagnostic engine operations."""


class DuplicateRuleError(DiagnosticEngineError):
    """Raised when registering a rule whose ID is already registered."""

    def __init__(self, rule_id: str, existing_version: str, attempted_version: str) -> None:
        super().__init__(
            f"Duplicate diagnostic rule ID '{rule_id}' already registered "
            f"(registered version: {existing_version}, attempted version: {attempted_version})."
        )
        self.rule_id = rule_id
        self.existing_version = existing_version
        self.attempted_version = attempted_version


class RuleNotFoundError(DiagnosticEngineError):
    """Raised when looking up an unregistered diagnostic rule ID."""

    def __init__(self, rule_id: str) -> None:
        super().__init__(f"Diagnostic rule '{rule_id}' was not found in the registry.")
        self.rule_id = rule_id


class InvalidRuleMetadataError(DiagnosticEngineError):
    """Raised when rule metadata fails validation requirements."""

    def __init__(self, rule_id: str, reason: str) -> None:
        super().__init__(f"Invalid metadata for rule '{rule_id}': {reason}")
        self.rule_id = rule_id
        self.reason = reason


class ResourceLimitExceededError(DiagnosticEngineError):
    """Raised when schema complexity exceeds configured diagnostic limits."""

    def __init__(self, resource: str, current: int, limit: int) -> None:
        super().__init__(
            f"Diagnostic resource limit exceeded for '{resource}': {current} > {limit}."
        )
        self.resource = resource
        self.current = current
        self.limit = limit


class InvalidContextError(DiagnosticEngineError):
    """Raised when a diagnostic context is missing required prerequisites."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Invalid diagnostic evaluation context: {reason}")
        self.reason = reason


class RuleEvaluationError(DiagnosticEngineError):
    """Encapsulates an unexpected failure encountered during rule evaluation."""

    def __init__(self, rule_id: str, original_exception: Exception) -> None:
        super().__init__(
            f"Rule '{rule_id}' evaluation failed with {type(original_exception).__name__}: {original_exception}"
        )
        self.rule_id = rule_id
        self.original_exception = original_exception
