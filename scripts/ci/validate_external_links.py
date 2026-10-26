#!/usr/bin/env python3
"""External HTTP/HTTPS link validator for DERA documentation.

Validates external web links with timeouts, retries, user-agent headers,
and explicit exclusion policies.

Note: This script is intended for scheduled or manual maintenance runs.
It is explicitly separated from deterministic PR CI gates.

Copyright (c) 2026 Krishanth. All rights reserved.
Licensed under the MIT License.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

# External link regex matching [text](http...)
EXTERNAL_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")

# Exclusion rules with explicit documented reasons
EXCLUSIONS: list[tuple[re.Pattern, str]] = [
    # 1. Private security advisory creation requires authenticated GitHub maintainer session
    (
        re.compile(r"^https://github\.com/krishanth7/dera/security/advisories/new"),
        "Requires authenticated GitHub login",
    ),
    # 2. Shields.io badge CDN rate-limits automated HEAD requests
    (
        re.compile(r"^https://img\.shields\.io/"),
        "Dynamic badge endpoint (frequently rate-limits)",
    ),
    # 3. Standard RFC 2606 illustrative domain names
    (
        re.compile(r"^https?://(?:www\.)?example\.(?:com|org|net)"),
        "RFC 2606 reserved illustrative domain",
    ),
    # 4. Localhost and loopback bindings used in documentation technical examples
    (
        re.compile(r"^https?://(?:127\.0\.0\.1|localhost)"),
        "Loopback/localhost development binding",
    ),
]

USER_AGENT = "DERA-DocsValidator/1.0 (+https://github.com/krishanth7/dera)"


def is_excluded(url: str) -> tuple[bool, str]:
    """Checks whether a URL matches documented exclusion patterns."""
    for pattern, reason in EXCLUSIONS:
        if pattern.search(url):
            return True, reason
    return False, ""


def check_url(url: str, timeout: float = 6.0, retries: int = 1) -> tuple[str, bool, int, str]:
    """Validates a single external URL via HTTP HEAD/GET request.

    Returns:
        (url, is_ok, status_code, message)
    """
    excluded, reason = is_excluded(url)
    if excluded:
        return url, True, 200, f"EXCLUDED: {reason}"

    # Disallow internal network IP addresses
    parsed = urllib.parse.urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if hostname.startswith(("10.", "192.168.", "172.16.", "172.17.", "172.18.", "172.19.", "172.2", "172.3")):
        return url, False, 403, "BLOCKED: Private network IP addresses are disallowed"

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
    }

    last_error = ""
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers, method="HEAD")
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return url, True, response.status, "OK"
        except urllib.error.HTTPError as exc:
            # 405 Method Not Allowed or 403 sometimes returned for HEAD; retry with GET
            if exc.code in {403, 405}:
                try:
                    req = urllib.request.Request(url, headers=headers, method="GET")
                    with urllib.request.urlopen(req, timeout=timeout) as response:
                        return url, True, response.status, "OK (via GET fallback)"
                except Exception as get_exc:
                    last_error = f"HTTP {exc.code} (GET failed: {get_exc})"
            else:
                last_error = f"HTTP {exc.code}: {exc.reason}"
        except urllib.error.URLError as exc:
            last_error = f"Connection error: {exc.reason}"
        except Exception as exc:
            last_error = f"Error: {exc}"

    return url, False, 0, last_error


def collect_external_links(repo_root: Path) -> dict[str, list[tuple[Path, int]]]:
    """Finds all external markdown links across documentation files."""
    url_occurrences: dict[str, list[tuple[Path, int]]] = {}

    files_to_scan: list[Path] = []
    for root_file in ["README.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md"]:
        p = repo_root / root_file
        if p.is_file():
            files_to_scan.append(p)

    docs_dir = repo_root / "docs"
    if docs_dir.is_dir():
        for p in docs_dir.rglob("*.md"):
            if "fixtures" not in p.parts:
                files_to_scan.append(p)

    for file_path in files_to_scan:
        try:
            content = file_path.read_text(encoding="utf-8")
            # Strip code blocks to avoid scanning example URLs
            clean_lines: list[str] = []
            in_code = False
            for line in content.splitlines():
                if line.strip().startswith("```"):
                    in_code = not in_code
                    clean_lines.append("")
                elif in_code:
                    clean_lines.append("")
                else:
                    clean_lines.append(line)
            masked = "\n".join(clean_lines)

            for match in EXTERNAL_LINK_PATTERN.finditer(masked):
                url = match.group(2).strip()
                line_no = masked[:match.start()].count("\n") + 1
                if url not in url_occurrences:
                    url_occurrences[url] = []
                url_occurrences[url].append((file_path, line_no))
        except Exception:
            pass

    return url_occurrences


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate external documentation links for DERA."
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Maximum concurrent network workers (default: 5).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=6.0,
        help="HTTP request timeout in seconds (default: 6.0).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List discovered URLs and exclusion status without making network calls.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent.parent
    url_map = collect_external_links(repo_root)

    print(f"Discovered {len(url_map)} unique external URLs across documentation.")

    if args.dry_run:
        print("\n[Dry Run] Discovered URLs:")
        for url in sorted(url_map.keys()):
            excluded, reason = is_excluded(url)
            status = f"EXCLUDED ({reason})" if excluded else "ACTIVE"
            print(f"  [{status}] {url} ({len(url_map[url])} occurrences)")
        return 0

    print(f"Checking {len(url_map)} URLs with concurrency {args.concurrency}...")

    failures: list[tuple[str, str, list[tuple[Path, int]]]] = []
    passed = 0
    excluded_count = 0

    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = {
            executor.submit(check_url, url, args.timeout, 1): url
            for url in url_map.keys()
        }

        for future in as_completed(futures):
            url = futures[future]
            try:
                checked_url, is_ok, code, msg = future.result()
                if "EXCLUDED" in msg:
                    excluded_count += 1
                elif is_ok:
                    passed += 1
                else:
                    failures.append((url, msg, url_map[url]))
            except Exception as exc:
                failures.append((url, str(exc), url_map[url]))

    print(f"\nExternal Link Validation Results:")
    print(f"  Active Verified: {passed}")
    print(f"  Excluded/Policy: {excluded_count}")
    print(f"  Failed:          {len(failures)}")

    if failures:
        print(f"\nFailed URLs ({len(failures)}):", file=sys.stderr)
        for url, reason, occurrences in failures:
            print(f"\n  URL: {url}", file=sys.stderr)
            print(f"  Reason: {reason}", file=sys.stderr)
            for file_path, line in occurrences[:3]:
                print(f"    - {file_path}:{line}", file=sys.stderr)
        return 1

    print("\nSUCCESS: All external links are reachable or properly documented in exclusions.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
