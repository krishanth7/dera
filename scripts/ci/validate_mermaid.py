#!/usr/bin/env python3
"""Validates syntax and structural balance of Mermaid diagrams in DERA documentation.

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

# Supported Mermaid diagram types
VALID_DIAGRAM_TYPES = {
    "flowchart",
    "graph",
    "sequencediagram",
    "classdiagram",
    "statediagram",
    "statediagram-v2",
    "erdiagram",
    "gantt",
    "pie",
    "gitgraph",
    "journey",
    "mindmap",
    "timeline",
    "quadrantchart",
    "requirementdiagram",
    "c4context",
    "c4container",
    "c4component",
    "sankey-beta",
    "block-beta",
    "xychart-beta",
}

# Regex to find fenced mermaid code blocks: ```mermaid ... ```
MERMAID_BLOCK_PATTERN = re.compile(
    r"^```mermaid[ \t]*\r?\n(.*?)\r?\n```",
    re.MULTILINE | re.DOTALL,
)


class MermaidValidationError:
    """Represents a diagnostic error in a Mermaid diagram."""

    def __init__(self, file_path: Path, line_number: int, code: str, message: str) -> None:
        self.file_path = file_path
        self.line_number = line_number
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line_number}: ERROR {self.code}: {self.message}"


def validate_mermaid_source(source: str, file_path: Path, start_line: int) -> list[MermaidValidationError]:
    """Validates the syntax and structural integrity of a single Mermaid diagram source."""
    errors: list[MermaidValidationError] = []
    lines = source.splitlines()

    # 1. Filter out empty lines and comments (%%)
    non_comment_lines: list[tuple[int, str]] = []
    for idx, raw_line in enumerate(lines):
        line = raw_line.strip()
        if line and not line.startswith("%%"):
            non_comment_lines.append((start_line + idx + 1, line))

    if not non_comment_lines:
        errors.append(
            MermaidValidationError(
                file_path,
                start_line,
                "MERMAID-004",
                "Empty Mermaid diagram block.",
            )
        )
        return errors

    # 2. Check diagram declaration type
    first_line_no, first_line = non_comment_lines[0]
    tokens = first_line.split()
    declaration = tokens[0].lower() if tokens else ""

    if declaration not in VALID_DIAGRAM_TYPES:
        errors.append(
            MermaidValidationError(
                file_path,
                first_line_no,
                "MERMAID-001",
                f"Unknown or unsupported Mermaid diagram type '{tokens[0]}'. "
                f"Supported types: {', '.join(sorted(VALID_DIAGRAM_TYPES)[:6])}...",
            )
        )
        return errors

    # 3. Structural validation based on diagram type
    if declaration in {"flowchart", "graph"}:
        subgraph_stack: list[tuple[int, str]] = []
        for line_no, line in non_comment_lines[1:]:
            # Check for subgraph opening
            if re.match(r"^subgraph\b", line, re.IGNORECASE):
                subgraph_stack.append((line_no, line))
            elif line.lower() == "end" or line.lower().startswith("end "):
                if not subgraph_stack:
                    errors.append(
                        MermaidValidationError(
                            file_path,
                            line_no,
                            "MERMAID-002",
                            "Unexpected 'end' directive without matching 'subgraph'.",
                        )
                    )
                else:
                    subgraph_stack.pop()

        if subgraph_stack:
            for unclosed_line, unclosed_text in subgraph_stack:
                errors.append(
                    MermaidValidationError(
                        file_path,
                        unclosed_line,
                        "MERMAID-002",
                        f"Unclosed 'subgraph' block: '{unclosed_text}'. Missing matching 'end'.",
                    )
                )

    elif declaration == "sequencediagram":
        block_stack: list[tuple[int, str]] = []
        for line_no, line in non_comment_lines[1:]:
            lower = line.lower()
            if re.match(r"^(loop|alt|opt|par|critical|rect|break)\b", lower):
                block_stack.append((line_no, line))
            elif lower == "end" or lower.startswith("end "):
                if not block_stack:
                    errors.append(
                        MermaidValidationError(
                            file_path,
                            line_no,
                            "MERMAID-002",
                            "Unexpected 'end' directive without matching block in sequence diagram.",
                        )
                    )
                else:
                    block_stack.pop()

        if block_stack:
            for unclosed_line, unclosed_text in block_stack:
                errors.append(
                    MermaidValidationError(
                        file_path,
                        unclosed_line,
                        "MERMAID-002",
                        f"Unclosed block in sequence diagram: '{unclosed_text}'. Missing matching 'end'.",
                    )
                )

    # 4. Bracket and Quote balance checks
    for line_no, line in non_comment_lines[1:]:
        # Skip comment lines
        if line.startswith("%%"):
            continue

        # Count unescaped double quotes
        quote_count = len(re.findall(r'(?<!\\)"', line))
        if quote_count % 2 != 0:
            errors.append(
                MermaidValidationError(
                    file_path,
                    line_no,
                    "MERMAID-003",
                    f"Unbalanced double quotes in Mermaid statement: {line}",
                )
            )

        # In flowcharts/graphs, check brackets outside quotes
        if declaration in {"flowchart", "graph"}:
            # Strip string literals before bracket checks
            stripped_line = re.sub(r'"[^"]*"', '""', line)
            
            # Check brackets
            if stripped_line.count("[") != stripped_line.count("]"):
                errors.append(
                    MermaidValidationError(
                        file_path,
                        line_no,
                        "MERMAID-003",
                        f"Unbalanced square brackets in Mermaid statement: {line}",
                    )
                )
            if stripped_line.count("(") != stripped_line.count(")"):
                errors.append(
                    MermaidValidationError(
                        file_path,
                        line_no,
                        "MERMAID-003",
                        f"Unbalanced parentheses in Mermaid statement: {line}",
                    )
                )

    return errors


def validate_markdown_file(file_path: Path) -> list[MermaidValidationError]:
    """Finds and validates all Mermaid diagram blocks in a markdown file."""
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [
            MermaidValidationError(
                file_path,
                1,
                "MERMAID-000",
                f"Invalid UTF-8 encoding: {exc}",
            )
        ]

    errors: list[MermaidValidationError] = []

    for match in MERMAID_BLOCK_PATTERN.finditer(content):
        # Calculate start line number
        start_line = content[:match.start()].count("\n") + 1
        diagram_source = match.group(1)
        block_errors = validate_mermaid_source(diagram_source, file_path, start_line)
        errors.extend(block_errors)

    return errors


def collect_markdown_files(repo_root: Path) -> list[Path]:
    """Discovers all documentation markdown files in the repository."""
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
            # Exclude fixtures if any
            if "fixtures" not in p.parts:
                doc_paths.append(p)

    return sorted(doc_paths)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Mermaid diagram syntax across DERA documentation."
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Validate a single specific markdown file.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent

    if args.file:
        files_to_check = [args.file.resolve()]
    else:
        files_to_check = collect_markdown_files(repo_root)

    total_diagrams = 0
    all_errors: list[MermaidValidationError] = []

    print(f"Scanning {len(files_to_check)} markdown documentation files for Mermaid diagrams...")

    for file_path in files_to_check:
        try:
            content = file_path.read_text(encoding="utf-8")
            diagram_count = len(MERMAID_BLOCK_PATTERN.findall(content))
            total_diagrams += diagram_count
            file_errors = validate_markdown_file(file_path)
            all_errors.extend(file_errors)
        except Exception as exc:
            all_errors.append(
                MermaidValidationError(file_path, 1, "MERMAID-ERR", f"Failed to scan file: {exc}")
            )

    print(f"Found {total_diagrams} Mermaid diagrams across {len(files_to_check)} files.")

    if all_errors:
        print(f"\nFAILED: Found {len(all_errors)} Mermaid diagram validation errors:", file=sys.stderr)
        for err in all_errors:
            print(f"  {err}", file=sys.stderr)
        return 1

    print(f"SUCCESS: All {total_diagrams} Mermaid diagrams passed syntax and structural validation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
