"""Tests for capability completeness assessment."""

from __future__ import annotations

import unittest

from dera.metadata.capabilities import assess_engine_metadata_completeness
from dera.metadata.enums import MetadataCompleteness


class TestCapabilities(unittest.TestCase):
    """Test suite for capability awareness and completeness mapping."""

    def test_complete_status(self) -> None:
        """Verify complete capability status."""
        status = assess_engine_metadata_completeness(
            engine="postgresql",
            feature_name="tables",
            capabilities={"tables": "supported"},
        )
        self.assertEqual(status, MetadataCompleteness.COMPLETE)

    def test_restricted_status(self) -> None:
        """Verify restricted visibility status."""
        status = assess_engine_metadata_completeness(
            engine="mysql",
            feature_name="views",
            capabilities={"views": "restricted"},
        )
        self.assertEqual(status, MetadataCompleteness.RESTRICTED)

    def test_unsupported_status(self) -> None:
        """Verify unsupported capability status."""
        status = assess_engine_metadata_completeness(
            engine="sqlite",
            feature_name="stored_procedures",
        )
        self.assertEqual(status, MetadataCompleteness.UNSUPPORTED)

    def test_sqlite_partial_checks(self) -> None:
        """Verify SQLite unnamed check constraint partial completeness."""
        status = assess_engine_metadata_completeness(
            engine="sqlite",
            feature_name="check_constraints",
        )
        self.assertEqual(status, MetadataCompleteness.PARTIAL)


if __name__ == "__main__":
    unittest.main()
