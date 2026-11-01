"""DERA Migration — Phase 9.2 Change Classifier.

Classifies Phase 9.1 SchemaChanges into structural categories and assesses
backward compatibility based on change types, property diffs, and type rules.
"""

from __future__ import annotations

from dera.comparison.enums import ComparisonChangeType, ComparisonObjectType
from dera.comparison.models import SchemaChange
from dera.migration.classification.models import ClassifiedChange
from dera.migration.compatibility.type_compatibility import (
    TypeConversionSafety,
    evaluate_type_conversion_safety,
)
from dera.migration.enums import (
    CompatibilityLevel,
    StructuralChangeCategory,
)


class ChangeClassifier:
    """Classifies SchemaChanges into structural categories and evaluates compatibility."""

    @classmethod
    def classify(cls, change: SchemaChange, engine: str = "postgresql") -> ClassifiedChange:
        """Classify a single SchemaChange."""
        category = cls._derive_category(change)
        compatibility, is_breaking, rationale = cls._evaluate_compatibility(
            change, category, engine
        )
        changed_props = tuple(d.property_name for d in change.property_differences)

        return ClassifiedChange(
            source_change_id=change.change_id,
            source_fingerprint=change.fingerprint,
            object_type=change.object_type,
            change_type=change.change_type,
            category=category,
            canonical_id=change.canonical_id,
            namespace=change.namespace,
            name=change.name,
            parent_name=change.parent_name,
            compatibility=compatibility,
            is_potentially_breaking=is_breaking,
            compatibility_rationale=rationale,
            changed_properties=changed_props,
        )

    @staticmethod
    def _derive_category(change: SchemaChange) -> StructuralChangeCategory:
        if change.change_type == ComparisonChangeType.REMOVED:
            return StructuralChangeCategory.REMOVAL
        if change.change_type == ComparisonChangeType.ADDED:
            return StructuralChangeCategory.ADDITIVE

        # Modified
        if change.object_type in (
            ComparisonObjectType.PRIMARY_KEY,
            ComparisonObjectType.FOREIGN_KEY,
            ComparisonObjectType.UNIQUE_CONSTRAINT,
            ComparisonObjectType.CHECK_CONSTRAINT,
        ):
            return StructuralChangeCategory.CONSTRAINT_CHANGE
        if change.object_type == ComparisonObjectType.INDEX:
            return StructuralChangeCategory.INDEX_CHANGE
        if change.object_type == ComparisonObjectType.RELATIONSHIP:
            return StructuralChangeCategory.RELATIONSHIP_CHANGE
        if change.object_type == ComparisonObjectType.NAMESPACE:
            return StructuralChangeCategory.NAMESPACE_CHANGE
        if change.object_type == ComparisonObjectType.VIEW:
            return StructuralChangeCategory.DEFINITION_CHANGE

        return StructuralChangeCategory.MODIFICATION

    @classmethod
    def _evaluate_compatibility(
        cls,
        change: SchemaChange,
        category: StructuralChangeCategory,
        engine: str,
    ) -> tuple[CompatibilityLevel, bool, str]:
        # 1. Removals
        if category == StructuralChangeCategory.REMOVAL:
            if change.object_type in (
                ComparisonObjectType.TABLE,
                ComparisonObjectType.COLUMN,
                ComparisonObjectType.PRIMARY_KEY,
                ComparisonObjectType.UNIQUE_CONSTRAINT,
                ComparisonObjectType.FOREIGN_KEY,
                ComparisonObjectType.VIEW,
            ):
                return (
                    CompatibilityLevel.POTENTIALLY_BREAKING,
                    True,
                    f"Removing {change.object_type.value} '{change.name}' will break queries, constraints, or applications depending on it.",
                )
            if change.object_type == ComparisonObjectType.INDEX:
                return (
                    CompatibilityLevel.REQUIRES_REVIEW,
                    False,
                    f"Removing index '{change.name}' may degrade query performance on underlying columns.",
                )
            return (
                CompatibilityLevel.REQUIRES_REVIEW,
                False,
                f"Removing {change.object_type.value} '{change.name}'.",
            )

        # 2. Additions
        if category == StructuralChangeCategory.ADDITIVE:
            if change.object_type == ComparisonObjectType.COLUMN:
                # Check nullability and default
                after_props = change.after_evidence.properties if change.after_evidence else {}
                is_nullable = after_props.get("is_nullable", True)
                default_expr = after_props.get("default_expression")
                if not is_nullable and default_expr is None:
                    return (
                        CompatibilityLevel.BREAKING_UNDER_STATED_CONDITIONS,
                        True,
                        f"Adding non-null column '{change.name}' without a default expression will fail on populated tables unless backfilled.",
                    )
                return (
                    CompatibilityLevel.COMPATIBLE_WITH_KNOWN_METADATA,
                    False,
                    f"Adding column '{change.name}' is backward-compatible with known metadata.",
                )

            if change.object_type in (
                ComparisonObjectType.PRIMARY_KEY,
                ComparisonObjectType.UNIQUE_CONSTRAINT,
                ComparisonObjectType.CHECK_CONSTRAINT,
            ):
                return (
                    CompatibilityLevel.BREAKING_UNDER_STATED_CONDITIONS,
                    True,
                    f"Adding constraint '{change.name}' requires existing rows to satisfy the condition; will fail if existing data violates it.",
                )

            if change.object_type == ComparisonObjectType.FOREIGN_KEY:
                return (
                    CompatibilityLevel.BREAKING_UNDER_STATED_CONDITIONS,
                    True,
                    f"Adding foreign key '{change.name}' requires all existing rows to reference valid parent records.",
                )

            return (
                CompatibilityLevel.COMPATIBLE_WITH_KNOWN_METADATA,
                False,
                f"Adding {change.object_type.value} '{change.name}' is backward-compatible with known metadata.",
            )

        # 3. Modifications
        if change.object_type == ComparisonObjectType.COLUMN:
            # Check type changes and nullability
            prop_diffs = {p.property_name: p for p in change.property_differences}
            if "native_data_type" in prop_diffs:
                diff = prop_diffs["native_data_type"]
                safety, explanation = evaluate_type_conversion_safety(
                    str(diff.before_value), str(diff.after_value), engine=engine
                )
                if safety == TypeConversionSafety.POTENTIAL_NARROWING:
                    return (
                        CompatibilityLevel.POTENTIALLY_BREAKING,
                        True,
                        f"Column type change: {explanation}",
                    )
                if safety == TypeConversionSafety.EXPLICIT_CONVERSION_REQUIRED:
                    return (
                        CompatibilityLevel.REQUIRES_REVIEW,
                        True,
                        f"Column type change: {explanation}",
                    )

            if "is_nullable" in prop_diffs:
                diff = prop_diffs["is_nullable"]
                if diff.before_value is True and diff.after_value is False:
                    return (
                        CompatibilityLevel.BREAKING_UNDER_STATED_CONDITIONS,
                        True,
                        f"Changing column '{change.name}' from nullable to NOT NULL will fail if existing rows contain NULL values.",
                    )

        if change.object_type == ComparisonObjectType.PRIMARY_KEY:
            return (
                CompatibilityLevel.POTENTIALLY_BREAKING,
                True,
                f"Modifying primary key '{change.name}' alters table identity and affects foreign-key relationships.",
            )

        if change.object_type == ComparisonObjectType.VIEW:
            return (
                CompatibilityLevel.REQUIRES_REVIEW,
                False,
                f"Modifying view '{change.name}' query definition may change result columns or types for downstream queries.",
            )

        return (
            CompatibilityLevel.REQUIRES_REVIEW,
            False,
            f"Modifying {change.object_type.value} '{change.name}'.",
        )
