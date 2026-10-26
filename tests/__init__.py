"""DERA test suite package bootstrap.

Ensures all monorepo package source directories (packages/core, packages/connectors, apps/api)
are available on sys.path for test discovery across all operating systems.
"""

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SOURCE_DIRS = [
    os.path.join(_REPO_ROOT, "packages", "core", "src"),
    os.path.join(_REPO_ROOT, "packages", "connectors", "src"),
    os.path.join(_REPO_ROOT, "apps", "api", "src"),
]

for _dir in _SOURCE_DIRS:
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
