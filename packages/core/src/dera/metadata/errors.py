"""DERA Canonical Metadata Normalization & Identity — Error Taxonomy.

Hierarchical, typed error classes for normalization failures, reference mismatches,
identity collisions, invalid payloads, and unsupported dialect conversions.
"""

from __future__ import annotations

from dera_core.exceptions import DeraError


class MetadataNormalizationError(DeraError):
    """Base error for all metadata normalization and object identity failures."""


class InvalidConnectorMetadataError(MetadataNormalizationError):
    """Raised when connector metadata reports violate structural contracts."""


class UnsupportedMappingError(MetadataNormalizationError):
    """Raised when an engine-specific construct has no deterministic mapping."""


class IdentityConflictError(MetadataNormalizationError):
    """Raised when an object identity collides or has conflicting representations."""


class DuplicateIdentityError(IdentityConflictError):
    """Raised when multiple distinct objects resolve to an identical canonical ID."""


class MissingRequiredMetadataError(MetadataNormalizationError):
    """Raised when mandatory schema elements (e.g. table name or position) are missing."""


class InvalidReferenceError(MetadataNormalizationError):
    """Raised when an object references a non-existent parent table or column."""


class MetadataSerializationError(MetadataNormalizationError):
    """Raised when canonical metadata fails deterministic UTF-8 serialization."""


class MetadataLimitExceededError(MetadataNormalizationError):
    """Raised when metadata size or count exceeds configured security bounds."""
