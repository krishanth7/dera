"""Tests for DERA allowlisted filtering and sorting contracts (Phase 4.2)."""

from __future__ import annotations

import unittest

from dera_api.contracts.filtering import (
    FilterCondition,
    FilterOperator,
    FilterParams,
    SortOrder,
    SortParams,
)
from pydantic import ValidationError


class TestFilteringContracts(unittest.TestCase):
    """Validate SortParams and FilterParams security, allowlists, and bounds."""

    def test_sort_order_enum(self) -> None:
        """Verify supported sort orders."""
        self.assertEqual(SortOrder.ASC.value, "asc")
        self.assertEqual(SortOrder.DESC.value, "desc")

    def test_sort_params_valid(self) -> None:
        """Verify valid sort parameters."""
        sort1 = SortParams(field="created_at", order=SortOrder.DESC)
        self.assertEqual(sort1.field, "created_at")
        self.assertEqual(sort1.order, SortOrder.DESC)

        sort2 = SortParams(field="schema_name")
        self.assertEqual(sort2.order, SortOrder.ASC)

    def test_sort_params_rejects_sql_injection(self) -> None:
        """Verify field validator prevents SQL injection patterns."""
        injection_candidates = [
            "name; DROP TABLE users;--",
            "name OR 1=1",
            "name, password",
            "name' AND '1'='1",
            "name--",
            "../secret",
        ]
        for candidate in injection_candidates:
            with self.subTest(candidate=candidate):
                with self.assertRaises(ValidationError):
                    SortParams(field=candidate)

    def test_filter_operators_completeness(self) -> None:
        """Verify allowlisted comparison operators."""
        expected_ops = {
            "eq",
            "neq",
            "gt",
            "gte",
            "lt",
            "lte",
            "in",
            "like",
            "ilike",
            "is_null",
            "is_not_null",
        }
        actual_ops = {op.value for op in FilterOperator}
        self.assertEqual(expected_ops, actual_ops)

    def test_filter_condition_valid(self) -> None:
        """Verify FilterCondition instantiation."""
        cond = FilterCondition(
            field="table_type",
            operator=FilterOperator.EQ,
            value="BASE TABLE",
        )
        self.assertEqual(cond.field, "table_type")
        self.assertEqual(cond.operator, FilterOperator.EQ)
        self.assertEqual(cond.value, "BASE TABLE")

    def test_filter_condition_rejects_injection_field(self) -> None:
        """Verify field names in FilterCondition are validated."""
        with self.assertRaises(ValidationError):
            FilterCondition(
                field="schema_name; DROP TABLE users",
                operator=FilterOperator.EQ,
                value="test",
            )

    def test_filter_params_bounded_complexity(self) -> None:
        """Verify max 20 conditions per filter payload to prevent DoS."""
        valid_conditions = [
            FilterCondition(field=f"col_{i}", operator=FilterOperator.EQ, value=f"val_{i}")
            for i in range(20)
        ]
        filter_params = FilterParams(conditions=valid_conditions)
        self.assertEqual(len(filter_params.conditions), 20)

        oversized_conditions = [
            FilterCondition(field=f"col_{i}", operator=FilterOperator.EQ, value=f"val_{i}")
            for i in range(21)
        ]
        with self.assertRaises(ValidationError):
            FilterParams(conditions=oversized_conditions)
