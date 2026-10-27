#!/usr/bin/env python3
"""Comprehensive documentation validation for DERA.

Validates internal links, heading anchors, UTF-8 encoding, documentation structure,
code fences, case sensitivity, and technical consistency.

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
from pathlib import Path
from typing import NamedTuple

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None  # Optional check if pyyaml is installed


class ValidationError(NamedTuple):
    file_path: Path
    line_number: int
    code: str
    message: str

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line_number}: ERROR {self.code}: {self.message}"


# Markdown link pattern: [text](target)
LINK_PATTERN = re.compile(r"(?<!\!)\[([^\]]+)\]\(([^)]+)\)")
# Markdown image pattern: ![alt](target)
IMAGE_PATTERN = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
# Heading pattern: # Heading
HEADING_PATTERN = re.compile(r"^(#{1,6})[ \t]+(.+)$", re.MULTILINE)
# HTML anchor tags: <a id="foo"> or <a name="foo">
HTML_ANCHOR_PATTERN = re.compile(
    r'<[a-zA-Z0-9]+[^>]+(?:id|name)=["\']([^"\']+)["\']', re.IGNORECASE
)

# Mandatory documentation entry points
MANDATORY_STRUCTURE = [
    "README.md",
    "docs/README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "LICENSE",
    "docs/architecture/README.md",
    "docs/development/README.md",
    "docs/i18n/languages.json",
]


def strip_markdown_inline(text: str) -> str:
    """Strips bold, italic, code, and link markdown syntax to get plain text."""
    # Strip links [text](url) -> text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Strip bold/italic
    text = re.sub(r"[*_~`]", "", text)
    return text.strip()


def github_slugify(heading_text: str) -> str:
    """Computes the primary GitHub markdown slug for a heading."""
    clean = strip_markdown_inline(heading_text).lower()
    # Remove punctuation stripped by GitHub
    clean = re.sub(r"[!\"#$%&'()*+,./:;<=>?@\[\\\]^_`{|}~]", "", clean)
    # Convert whitespace to hyphens
    slug = re.sub(r"\s+", "-", clean)
    # Strip leading/trailing hyphens
    return slug.strip("-")


def extract_headings_and_slugs(content: str) -> tuple[list[tuple[int, int, str]], set[str]]:
    """Extracts all headings and generates full GitHub-compatible anchor slugs.

    Returns:
        headings: list of (line_number, level, heading_text)
        slugs: set of valid anchor strings for the file
    """
    headings: list[tuple[int, int, str]] = []
    slugs: set[str] = set()
    slug_counts: dict[str, int] = {}

    lines = content.splitlines()
    in_code_block = False

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        # Check for HTML anchors
        for anchor_match in HTML_ANCHOR_PATTERN.finditer(line):
            slugs.add(anchor_match.group(1))

        # Check for markdown heading
        match = HEADING_PATTERN.match(line)
        if match:
            level = len(match.group(1))
            heading_text = match.group(2).strip()
            headings.append((idx, level, heading_text))

            base_slug = github_slugify(heading_text)
            count = slug_counts.get(base_slug, 0)
            slug_counts[base_slug] = count + 1

            if count == 0:
                current_slug = base_slug
            else:
                current_slug = f"{base_slug}-{count}"

            slugs.add(current_slug)

            # Generate GitHub-compatible emoji-stripped anchor variants
            # On GitHub, leading emojis are stripped, often leaving a leading hyphen from the following space
            emoji_pattern = re.compile(
                r"[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]|[\ufe00-\ufe0f]"
            )
            no_emoji = emoji_pattern.sub("", strip_markdown_inline(heading_text).lower())
            no_emoji_punct = re.sub(r"[!\"#$%&'()*+,./:;<=>?@\[\\\]^_`{|}~]", "", no_emoji)
            emoji_slug = re.sub(r"\s+", "-", no_emoji_punct)

            slugs.add(emoji_slug)
            slugs.add(emoji_slug.strip("-"))
            if emoji_slug.strip("-"):
                slugs.add(f"-{emoji_slug.strip('-')}")

            # Also handle word-tokenized slug for multi-language headings
            alphanumeric_words = re.findall(r"[\w-]+", heading_text.lower())
            if alphanumeric_words:
                plain_slug = "-".join(alphanumeric_words)
                slugs.add(plain_slug)
                slugs.add(f"-{plain_slug}")

    return headings, slugs


def check_case_sensitive_exists(target_path: Path, repo_root: Path) -> bool:
    """Verifies that target_path exists with exact case match on disk."""
    if not target_path.exists():
        return False

    try:
        abs_target = target_path.absolute()
        real_target = target_path.resolve()
        root_resolved = repo_root.resolve()

        # On Windows, resolve() normalizes casing to the real disk name.
        # If absolute parts do not match resolved parts, there is a case mismatch.
        try:
            rel_abs = abs_target.relative_to(root_resolved)
            rel_real = real_target.relative_to(root_resolved)
            if rel_abs.parts != rel_real.parts:
                return False
        except ValueError:
            pass

        # Also verify directly against directory children
        rel = abs_target.relative_to(root_resolved)
        current = root_resolved
        for part in rel.parts:
            children = os.listdir(current)
            if part not in children:
                return False
            current = current / part
        return True
    except Exception:
        return True


class DocValidator:
    """Validates markdown documentation across the repository."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve()
        self.file_slug_cache: dict[Path, set[str]] = {}

    def get_file_slugs(self, file_path: Path) -> set[str]:
        resolved = file_path.resolve()
        if resolved in self.file_slug_cache:
            return self.file_slug_cache[resolved]

        if not resolved.is_file():
            return set()

        try:
            content = resolved.read_text(encoding="utf-8")
            _, slugs = extract_headings_and_slugs(content)
            self.file_slug_cache[resolved] = slugs
            return slugs
        except Exception:
            return set()

    def validate_structure(self) -> list[ValidationError]:
        """Validates that mandatory documentation entry points exist."""
        errors: list[ValidationError] = []
        for rel_str in MANDATORY_STRUCTURE:
            target = self.repo_root / rel_str
            if not target.exists():
                errors.append(
                    ValidationError(
                        target,
                        1,
                        "DOC-STRUCT-007",
                        f"Mandatory documentation entry point does not exist: '{rel_str}'",
                    )
                )
            elif not check_case_sensitive_exists(target, self.repo_root):
                errors.append(
                    ValidationError(
                        target,
                        1,
                        "DOC-CASE-005",
                        f"Mandatory documentation entry point has case mismatch on disk: '{rel_str}'",
                    )
                )
        return errors

    def validate_technical_consistency(self) -> list[ValidationError]:
        """Validates consistency between documentation and configuration files."""
        errors: list[ValidationError] = []

        # Check pyproject.toml Python version vs README.md
        pyproject_path = self.repo_root / "pyproject.toml"
        readme_path = self.repo_root / "README.md"

        if pyproject_path.is_file() and readme_path.is_file():
            try:
                pyproject_text = pyproject_path.read_text(encoding="utf-8")
                readme_text = readme_path.read_text(encoding="utf-8")

                if 'requires-python = ">=3.12"' in pyproject_text:
                    if "Python 3.12" not in readme_text:
                        errors.append(
                            ValidationError(
                                readme_path,
                                1,
                                "DOC-CONS-008",
                                "README.md does not mention required Python version (Python 3.12).",
                            )
                        )
            except Exception as exc:
                errors.append(
                    ValidationError(
                        pyproject_path,
                        1,
                        "DOC-CONS-008",
                        f"Failed to check technical consistency: {exc}",
                    )
                )

        return errors

    def validate_code_fences(self, content: str, file_path: Path) -> list[ValidationError]:
        """Validates code fence balance and JSON/YAML embedded syntax."""
        errors: list[ValidationError] = []
        lines = content.splitlines()

        fence_open = False
        fence_line = 0
        fence_lang = ""
        block_lines: list[str] = []

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("```"):
                if not fence_open:
                    fence_open = True
                    fence_line = idx
                    fence_lang = stripped[3:].strip().lower()
                    block_lines = []
                else:
                    fence_open = False
                    # Validate block content if marked json or yaml
                    block_content = "\n".join(block_lines)
                    if fence_lang == "json" and block_content.strip():
                        try:
                            json.loads(block_content)
                        except json.JSONDecodeError as exc:
                            errors.append(
                                ValidationError(
                                    file_path,
                                    fence_line,
                                    "DOC-CODE-006",
                                    f"Invalid JSON in fenced code block starting at line {fence_line}: {exc}",
                                )
                            )
                    elif fence_lang in {"yaml", "yml"} and block_content.strip() and yaml:
                        try:
                            yaml.safe_load(block_content)
                        except Exception as exc:
                            errors.append(
                                ValidationError(
                                    file_path,
                                    fence_line,
                                    "DOC-CODE-006",
                                    f"Invalid YAML in fenced code block starting at line {fence_line}: {exc}",
                                )
                            )
                    block_lines = []
            elif fence_open:
                block_lines.append(line)

        if fence_open:
            errors.append(
                ValidationError(
                    file_path,
                    fence_line,
                    "DOC-CODE-006",
                    f"Unclosed code fence starting at line {fence_line}.",
                )
            )

        return errors

    def validate_file(self, file_path: Path) -> list[ValidationError]:
        """Performs full internal validation of a single markdown documentation file."""
        errors: list[ValidationError] = []

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            return [
                ValidationError(
                    file_path,
                    1,
                    "DOC-ENC-001",
                    f"Invalid UTF-8 encoding: {exc}",
                )
            ]

        # 1. Code fence validation
        errors.extend(self.validate_code_fences(content, file_path))

        # 2. Heading hierarchy and local slug extraction
        headings, local_slugs = extract_headings_and_slugs(content)
        self.file_slug_cache[file_path.resolve()] = local_slugs

        # Top-level documents must have an H1 heading (#)
        if not headings:
            errors.append(
                ValidationError(
                    file_path,
                    1,
                    "DOC-HEAD-002",
                    "No markdown headings found in document.",
                )
            )

        # 3. Mask out fenced code blocks and inline code for link extraction
        # to avoid false positives on documentation examples like `[text](url)`
        lines = content.splitlines()
        clean_lines: list[str] = []
        in_code_block = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                clean_lines.append("")
                continue

            if in_code_block:
                clean_lines.append("")
            else:
                # Replace inline backtick code spans with spaces of equal length
                clean_line = re.sub(r"`[^`]+`", lambda m: " " * len(m.group(0)), line)
                clean_lines.append(clean_line)

        masked_content = "\n".join(clean_lines)

        # 4. Link & Image Validation
        for match in LINK_PATTERN.finditer(masked_content):
            link_text = match.group(1).strip()
            raw_target = match.group(2).strip()

            line_number = masked_content[: match.start()].count("\n") + 1

            # Ignore empty targets or mailto / external http(s)
            if not raw_target or raw_target.startswith(("http://", "https://", "mailto:")):
                continue

            # Local anchor fragment in current file
            if raw_target.startswith("#"):
                anchor = urllib.parse.unquote(raw_target[1:]).strip()
                if anchor and anchor not in local_slugs:
                    errors.append(
                        ValidationError(
                            file_path,
                            line_number,
                            "DOC-ANCH-004",
                            f"Local anchor '#{anchor}' not found in document headings. (Link: [{link_text}]({raw_target}))",
                        )
                    )
                continue

            # Target containing path and optional anchor
            parts = raw_target.split("#", 1)
            raw_path = parts[0]
            anchor = urllib.parse.unquote(parts[1]).strip() if len(parts) > 1 else None

            # Unquote URL-encoded spaces / characters
            unquoted_path = urllib.parse.unquote(raw_path)

            if raw_path.startswith("/"):
                # Absolute repository-root link
                target_path = (self.repo_root / unquoted_path.lstrip("/")).resolve()
            else:
                # Relative link
                target_path = (file_path.parent / unquoted_path).resolve()

            # Verify target exists on disk
            if not target_path.exists():
                errors.append(
                    ValidationError(
                        file_path,
                        line_number,
                        "DOC-LINK-003",
                        f"Target path does not exist: '{raw_target}' (Resolved: '{target_path}')",
                    )
                )
                continue

            # Case-sensitivity check
            if not check_case_sensitive_exists(target_path, self.repo_root):
                errors.append(
                    ValidationError(
                        file_path,
                        line_number,
                        "DOC-CASE-005",
                        f"Case mismatch for target path on disk: '{raw_target}' (Resolved: '{target_path}')",
                    )
                )

            # Anchor check in target markdown file
            if anchor and target_path.is_file() and target_path.suffix.lower() == ".md":
                target_slugs = self.get_file_slugs(target_path)
                if anchor not in target_slugs:
                    errors.append(
                        ValidationError(
                            file_path,
                            line_number,
                            "DOC-ANCH-004",
                            f"Anchor '#{anchor}' not found in target file '{target_path.name}'. (Link: [{link_text}]({raw_target}))",
                        )
                    )

        return errors


def collect_markdown_files(repo_root: Path) -> list[Path]:
    """Discovers all markdown documentation files to be validated."""
    doc_paths: list[Path] = []

    # Root documentation files
    for root_file in ["README.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md"]:
        p = repo_root / root_file
        if p.is_file():
            doc_paths.append(p)

    # docs/ hierarchy
    docs_dir = repo_root / "docs"
    if docs_dir.is_dir():
        for p in docs_dir.rglob("*.md"):
            if "fixtures" not in p.parts:
                doc_paths.append(p)

    return sorted(doc_paths)


def main() -> int:
    parser = argparse.ArgumentParser(description="Comprehensive documentation validator for DERA.")
    parser.add_argument(
        "--file",
        type=Path,
        help="Validate a single specific markdown file.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    validator = DocValidator(repo_root)

    all_errors: list[ValidationError] = []

    struct_errors: list[ValidationError] = []
    cons_errors: list[ValidationError] = []

    # 1. Structure validation
    if not args.file:
        struct_errors = validator.validate_structure()
        all_errors.extend(struct_errors)

        # 2. Technical consistency
        cons_errors = validator.validate_technical_consistency()
        all_errors.extend(cons_errors)

    # 3. File validation
    if args.file:
        files_to_check = [args.file.resolve()]
    else:
        files_to_check = collect_markdown_files(repo_root)

    print(f"Validating {len(files_to_check)} markdown documentation files...")

    file_errors: list[ValidationError] = []
    for file_path in files_to_check:
        errs = validator.validate_file(file_path)
        file_errors.extend(errs)

    all_errors.extend(file_errors)

    # Domain evaluations
    struct_status = "PASS" if not struct_errors else "FAIL"
    cons_status = "PASS" if not cons_errors else "FAIL"
    link_errs = [e for e in file_errors if e.code.startswith("DOC-LINK")]
    anch_errs = [e for e in file_errors if e.code.startswith("DOC-ANCH")]
    fence_errs = [e for e in file_errors if e.code.startswith("DOC-FENCE")]

    link_status = "PASS" if not link_errs else "FAIL"
    anch_status = "PASS" if not anch_errs else "FAIL"
    fence_status = "PASS" if not fence_errs else "FAIL"
    overall_status = "PASS" if not all_errors else "FAIL"

    print("\nDERA Documentation CI")
    print("=====================")
    print(f"Documentation structure:    {struct_status}")
    print(f"Technical consistency:      {cons_status}")
    print(f"Internal links:             {link_status}")
    print(f"Heading anchors:            {anch_status}")
    print(f"Code fence integrity:       {fence_status}")
    print(f"Overall: {overall_status}\n")

    if all_errors:
        print(f"FAILED: Found {len(all_errors)} documentation validation issues:", file=sys.stderr)
        for err in all_errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    print(f"SUCCESS: All {len(files_to_check)} markdown documentation files passed validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
