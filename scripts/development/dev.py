#!/usr/bin/env python3
"""DERA — Cross-Platform Development CLI.

Provides unified commands for building, linting, testing, and running DERA
monorepo workspaces across Windows, Linux, and macOS.
"""

import argparse
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_cmd(cmd: list[str], cwd: str = REPO_ROOT) -> int:
    """Execute a system command and return exit code."""
    print(f"\n[DERA-DEV] Executing: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, shell=(os.name == "nt"))
    return result.returncode



def cmd_test(args: argparse.Namespace) -> int:
    """Run unit, integration, and architecture test suites."""
    return run_cmd([sys.executable, "-m", "unittest", "discover", "tests/"])


def cmd_typecheck(args: argparse.Namespace) -> int:
    """Run TypeScript compiler static typecheck."""
    return run_cmd(["npx", "-p", "typescript", "tsc", "--noEmit"])


def cmd_compile(args: argparse.Namespace) -> int:
    """Compile all Python packages and apps."""
    return run_cmd([sys.executable, "-m", "compileall", "packages/", "apps/", "tests/"])


def cmd_validate_docs(args: argparse.Namespace) -> int:
    """Run documentation link and internationalization parity checks."""
    code1 = run_cmd([sys.executable, "scripts/ci/validate_docs.py"])
    code2 = run_cmd([sys.executable, "scripts/ci/validate_i18n.py"])
    return code1 or code2


def cmd_all(args: argparse.Namespace) -> int:
    """Run full baseline validation suite (compile, test, typecheck, docs)."""
    checks = [
        ("Python Compile", cmd_compile),
        ("Tests", cmd_test),
        ("TypeScript Typecheck", cmd_typecheck),
        ("Documentation Validation", cmd_validate_docs),
    ]
    for name, fn in checks:
        print(f"\n>>> Running check: {name}...")
        code = fn(args)
        if code != 0:
            print(f"\n[FAIL]: {name} returned exit code {code}")
            return code
    print("\n[SUCCESS]: All development baseline checks passed successfully.")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="DERA Cross-Platform Development & Architecture CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("test", help="Run Python test suites")
    subparsers.add_parser("typecheck", help="Run TypeScript type checking")
    subparsers.add_parser("compile", help="Compile Python packages")
    subparsers.add_parser("validate-docs", help="Validate documentation links and i18n parity")
    subparsers.add_parser("all", help="Run all verification checks")

    args = parser.parse_args()

    commands = {
        "test": cmd_test,
        "typecheck": cmd_typecheck,
        "compile": cmd_compile,
        "validate-docs": cmd_validate_docs,
        "all": cmd_all,
    }

    exit_code = commands[args.command](args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
