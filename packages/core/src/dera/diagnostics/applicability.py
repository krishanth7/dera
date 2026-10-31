"""DERA Diagnostics — Rule Applicability Verification.

Evaluates whether a diagnostic rule can execute against a target context,
distinguishing supported rules from unsupported engines or insufficient metadata.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from dera.diagnostics.enums import ApplicabilityStatus

if TYPE_CHECKING:
    from dera.diagnostics.context import DiagnosticContext
    from dera.diagnostics.protocols import DiagnosticRule


def check_rule_applicability(
    rule: DiagnosticRule, context: DiagnosticContext
) -> tuple[ApplicabilityStatus, str]:
    """Determines if a rule can execute against the given DiagnosticContext.

    Returns:
        tuple[ApplicabilityStatus, str]: The evaluation readiness and explanatory reason.
    """
    metadata = rule.metadata

    # 1. Database engine compatibility
    if metadata.supported_engines:
        norm_source_engine = context.source_engine.lower()
        supported_norm = {eng.lower() for eng in metadata.supported_engines}
        if norm_source_engine != "unknown" and norm_source_engine not in supported_norm:
            return (
                ApplicabilityStatus.UNSUPPORTED,
                f"Rule '{metadata.rule_id}' supports engines {list(metadata.supported_engines)}, "
                f"but source engine is '{context.source_engine}'.",
            )

    # 2. Required capability verification
    if metadata.required_capabilities and context.capabilities is not None:
        missing_capabilities = []
        for cap in metadata.required_capabilities:
            cap_state = context.capabilities.get_state(cap)
            # If the capability state is UNSUPPORTED, rule cannot run
            if cap_state.value == "UNSUPPORTED":
                return (
                    ApplicabilityStatus.UNSUPPORTED,
                    f"Required capability '{cap}' is unsupported by the schema capability profile.",
                )
            if cap_state.value in ("UNTESTED", "PARTIAL", "FAILED"):
                missing_capabilities.append(cap)

        if missing_capabilities:
            return (
                ApplicabilityStatus.INSUFFICIENT_METADATA,
                f"Required capabilities {missing_capabilities} have incomplete or untested metadata.",
            )

    # 3. Metadata completeness verification
    completeness_str = getattr(context.completeness, "value", str(context.completeness)).lower()
    if completeness_str == "restricted":
        # If the rule requires deep structural integrity, restricted completeness flags insufficient metadata
        if "metadata_completeness" in metadata.required_capabilities:
            return (
                ApplicabilityStatus.INSUFFICIENT_METADATA,
                f"Context has RESTRICTED metadata completeness; rule '{metadata.rule_id}' requires complete metadata.",
            )

    return ApplicabilityStatus.APPLICABLE, "Rule is applicable for evaluation."
