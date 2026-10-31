"""DERA Reverse Engineering — Phase 6.6 Export Error Taxonomy.

Defines strongly typed exceptions for export validation, format support,
resource limits, and security enforcement.
"""

from __future__ import annotations


class ExportError(Exception):
    """Base exception for all export-related failures."""


class UnsupportedExportFormatError(ExportError):
    """Raised when an unrecognized or unsupported export format is requested."""


class ExportResourceLimitError(ExportError):
    """Raised when an export operation exceeds configured memory, size, or object limits."""


class ExportValidationError(ExportError):
    """Raised when export options, scope, or input models fail validation."""


class ExportSecurityError(ExportError):
    """Raised when potential injection attacks or security violations are detected."""
