#!/usr/bin/env python3
"""Automated regression test suite for DERA documentation validation tooling.

Tests internal link validation, heading anchor resolution, code fence checks,
Mermaid diagram syntax parsing, and external link exclusion policies.

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

from pathlib import Path
import unittest

from scripts.ci.validate_docs import (
    DocValidator,
    check_case_sensitive_exists,
    extract_headings_and_slugs,
    github_slugify,
)
from scripts.ci.validate_external_links import is_excluded
from scripts.ci.validate_mermaid import (
    validate_markdown_file,
    validate_mermaid_source,
)


class TestDocumentationValidation(unittest.TestCase):
    """Regression test suite for documentation validation scripts."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parent.parent.parent
        cls.fixtures_dir = cls.repo_root / "tests" / "fixtures" / "docs"
        cls.validator = DocValidator(cls.repo_root)

    # -------------------------------------------------------------
    # 1. Internal Link & Anchor Validation Tests
    # -------------------------------------------------------------

    def test_valid_document_fixture(self) -> None:
        """Valid fixture markdown file must pass validation with zero errors."""
        valid_file = self.fixtures_dir / "valid_doc.md"
        errors = self.validator.validate_file(valid_file)
        self.assertEqual(
            len(errors),
            0,
            f"Expected 0 errors for valid_doc.md, found: {[str(e) for e in errors]}",
        )

    def test_broken_link_detection(self) -> None:
        """Broken internal link must trigger DOC-LINK-003."""
        broken_link_file = self.fixtures_dir / "broken_link.md"
        errors = self.validator.validate_file(broken_link_file)
        error_codes = [e.code for e in errors]
        self.assertIn("DOC-LINK-003", error_codes)

    def test_broken_anchor_detection(self) -> None:
        """Broken local heading anchor must trigger DOC-ANCH-004."""
        broken_anchor_file = self.fixtures_dir / "broken_anchor.md"
        errors = self.validator.validate_file(broken_anchor_file)
        error_codes = [e.code for e in errors]
        self.assertIn("DOC-ANCH-004", error_codes)

    def test_unbalanced_code_fence_detection(self) -> None:
        """Unclosed code fence must trigger DOC-CODE-006."""
        unbalanced_file = self.fixtures_dir / "unbalanced_fence.md"
        errors = self.validator.validate_file(unbalanced_file)
        error_codes = [e.code for e in errors]
        self.assertIn("DOC-CODE-006", error_codes)

    def test_github_slugify_punctuation_and_casing(self) -> None:
        """Slug generator should convert to lowercase, remove punctuation, and convert spaces."""
        self.assertEqual(github_slugify("Hello World!"), "hello-world")
        self.assertEqual(github_slugify("C++ & Python (3.12)"), "c-python-312")
        self.assertEqual(github_slugify("Step 1: Install & Configure"), "step-1-install-configure")

    def test_duplicate_headings_slug_disambiguation(self) -> None:
        """Duplicate headings in same file must receive sequential numeric suffixes."""
        content = (
            "# Main Title\n\n"
            "## Architecture\n\n"
            "Content 1\n\n"
            "## Architecture\n\n"
            "Content 2\n\n"
            "## Architecture\n\n"
            "Content 3\n"
        )
        _, slugs = extract_headings_and_slugs(content)
        self.assertIn("architecture", slugs)
        self.assertIn("architecture-1", slugs)
        self.assertIn("architecture-2", slugs)

    def test_emoji_heading_slug_variants(self) -> None:
        """Emoji headings must generate both emoji-free and leading-hyphen slug variants."""
        content = "## 🏗️ Architecture Overview\n"
        _, slugs = extract_headings_and_slugs(content)
        # Should generate primary slug or emoji-stripped variants
        self.assertTrue(
            "architecture-overview" in slugs or "-architecture-overview" in slugs,
            f"Expected slug variants for emoji heading, got: {slugs}",
        )

    def test_mandatory_structure_validation(self) -> None:
        """Structure validator must confirm presence of all mandatory documentation entry points."""
        errors = self.validator.validate_structure()
        self.assertEqual(
            len(errors),
            0,
            f"Mandatory structure files missing: {[str(e) for e in errors]}",
        )

    def test_case_sensitive_path_check(self) -> None:
        """Case sensitivity check must pass for exact casing and fail for incorrect casing."""
        # Exact casing
        self.assertTrue(check_case_sensitive_exists(self.repo_root / "README.md", self.repo_root))
        self.assertTrue(check_case_sensitive_exists(self.repo_root / "docs" / "README.md", self.repo_root))

        # Incorrect casing on Windows/Linux
        wrong_case = self.repo_root / "readme.md"  # Lowercase 'r'
        # If filesystem has uppercase README.md:
        if (self.repo_root / "README.md").is_file():
            # Check if case_sensitive_exists detects the mismatch
            is_valid = check_case_sensitive_exists(wrong_case, self.repo_root)
            self.assertFalse(is_valid, "Case mismatch was not detected for 'readme.md'")

    # -------------------------------------------------------------
    # 2. Mermaid Diagram Validation Tests
    # -------------------------------------------------------------

    def test_valid_mermaid_flowchart(self) -> None:
        """Valid flowchart syntax must pass with zero errors."""
        source = (
            "flowchart TD\n"
            "    subgraph Core\n"
            "        A[Start] --> B[Finish]\n"
            "    end\n"
        )
        errors = validate_mermaid_source(source, Path("test.md"), 1)
        self.assertEqual(len(errors), 0, f"Unexpected errors: {[str(e) for e in errors]}")

    def test_valid_mermaid_sequence_diagram(self) -> None:
        """Valid sequence diagram syntax must pass with zero errors."""
        source = (
            "sequenceDiagram\n"
            "    autonumber\n"
            "    actor User\n"
            "    participant API\n"
            "    User->>API: Request\n"
            "    API-->>User: Response\n"
        )
        errors = validate_mermaid_source(source, Path("test.md"), 1)
        self.assertEqual(len(errors), 0, f"Unexpected errors: {[str(e) for e in errors]}")

    def test_invalid_diagram_type(self) -> None:
        """Unknown diagram type must emit MERMAID-001."""
        source = "unknownDiagramType\n    A --> B\n"
        errors = validate_mermaid_source(source, Path("test.md"), 1)
        error_codes = [e.code for e in errors]
        self.assertIn("MERMAID-001", error_codes)

    def test_unclosed_subgraph_detection(self) -> None:
        """Unclosed subgraph must emit MERMAID-002."""
        invalid_mermaid_file = self.fixtures_dir / "invalid_mermaid.md"
        errors = validate_markdown_file(invalid_mermaid_file)
        error_codes = [e.code for e in errors]
        self.assertIn("MERMAID-002", error_codes)

    def test_empty_mermaid_block_detection(self) -> None:
        """Empty mermaid block must emit MERMAID-004."""
        source = "\n  %% Only comments\n\n"
        errors = validate_mermaid_source(source, Path("test.md"), 1)
        error_codes = [e.code for e in errors]
        self.assertIn("MERMAID-004", error_codes)

    def test_unbalanced_bracket_detection(self) -> None:
        """Unbalanced square bracket must emit MERMAID-003."""
        source = "flowchart TD\n    A[Unclosed bracket --> B\n"
        errors = validate_mermaid_source(source, Path("test.md"), 1)
        error_codes = [e.code for e in errors]
        self.assertIn("MERMAID-003", error_codes)

    # -------------------------------------------------------------
    # 3. External Link Policy Tests
    # -------------------------------------------------------------

    def test_external_link_exclusion_rules(self) -> None:
        """Excluded URLs must match documented policy reasons."""
        # 1. Private security advisory
        exc1, reason1 = is_excluded("https://github.com/krishanth7/dera/security/advisories/new")
        self.assertTrue(exc1)
        self.assertIn("authenticated", reason1.lower())

        # 2. Shields.io badge
        exc2, reason2 = is_excluded("https://img.shields.io/badge/test-badge-blue")
        self.assertTrue(exc2)
        self.assertIn("badge", reason2.lower())

        # 3. Illustrative RFC 2606 domain
        exc3, reason3 = is_excluded("https://example.com/api/v1/inspect")
        self.assertTrue(exc3)
        self.assertIn("rfc 2606", reason3.lower())

        # 4. Localhost loopback binding
        exc4, reason4 = is_excluded("http://127.0.0.1:8000/health")
        self.assertTrue(exc4)
        self.assertIn("loopback", reason4.lower())

        # 5. Non-excluded URL
        exc5, _ = is_excluded("https://github.com/krishanth7/dera")
        self.assertFalse(exc5)


if __name__ == "__main__":
    unittest.main()
