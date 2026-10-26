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
    code2 = run_cmd([sys.executable, "scripts/docs/generate_language_navigation.py", "--check"])
    code3 = run_cmd([sys.executable, "scripts/ci/validate_i18n.py"])
    return code1 or code2 or code3


def cmd_validate_title(args: argparse.Namespace) -> int:
    """Validate a commit or PR title against Conventional Commits."""
    title = getattr(args, "title", None)
    cmd = [sys.executable, "scripts/ci/validate_pr_title.py"]
    if title:
        cmd.append(title)
    return run_cmd(cmd)


def cmd_install_hooks(args: argparse.Namespace) -> int:
    """Install local Git hooks for commit message validation."""
    git_hooks_dir = os.path.join(REPO_ROOT, ".git", "hooks")
    if not os.path.isdir(git_hooks_dir):
        print(f"[FAIL]: Git hooks directory not found at {git_hooks_dir}. Are you in a Git repository?")
        return 1

    commit_msg_hook = os.path.join(git_hooks_dir, "commit-msg")
    hook_script = (
        "#!/usr/bin/env sh\n"
        "# DERA Local Commit Message Hook\n"
        'MSG=$(head -n 1 "$1")\n'
        'python scripts/ci/validate_pr_title.py "$MSG"\n'
    )

    try:
        with open(commit_msg_hook, "w", encoding="utf-8", newline="\n") as f:
            f.write(hook_script)
        # On POSIX, make executable
        if os.name != "nt":
            mode = os.stat(commit_msg_hook).st_mode
            os.chmod(commit_msg_hook, mode | 0o111)
        print(f"[SUCCESS]: Installed Conventional Commit hook at {commit_msg_hook}")
        return 0
    except OSError as err:
        print(f"[FAIL]: Could not install hook: {err}")
        return 1


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

    title_parser = subparsers.add_parser("validate-title", help="Validate commit/PR title against Conventional Commits")
    title_parser.add_argument("title", nargs="?", help="Commit or PR title string to validate")

    subparsers.add_parser("install-hooks", help="Install local Git commit-msg hook")
    subparsers.add_parser("all", help="Run all verification checks")

    args = parser.parse_args()

    commands = {
        "test": cmd_test,
        "typecheck": cmd_typecheck,
        "compile": cmd_compile,
        "validate-docs": cmd_validate_docs,
        "validate-title": cmd_validate_title,
        "install-hooks": cmd_install_hooks,
        "all": cmd_all,
    }

    exit_code = commands[args.command](args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

