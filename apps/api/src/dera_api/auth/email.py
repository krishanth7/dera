"""DERA Auth — Email Syntax Validation and Conservative Normalization.

Implements conservative email address normalization adhering to RFC 5321/5322.
Enforces:
- Syntax validation.
- Length bounds (min 5, max 255 chars).
- Domain normalization to lower case (DNS is case-insensitive).
- Localpart preserved without stripping dots or plus-address tags (prevents account aliasing collision).
- Documented canonical representation for database uniqueness comparison.
"""

import re

# Strict but practical RFC 5322 compliant regex pattern
_EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)


class EmailValidationError(ValueError):
    """Raised when an email address fails RFC syntax or length validation."""


def normalize_email(email: str) -> str:
    """Validate syntax and conservatively normalize an email address.

    Normalization policy:
    1. Strip leading and trailing whitespace.
    2. Enforce length: total length <= 254 characters (RFC 5321 limit).
    3. Separate local-part and domain-part at the last '@'.
    4. Validate local-part length <= 64 characters.
    5. Convert domain-part to lowercase (domains are case-insensitive per DNS).
    6. Convert local-part to lowercase for consistent identity comparison,
       while STRICTLY PRESERVING dots and '+' subaddressing (never strip '+tag' or dots).
    7. Validate overall syntax against standard email pattern.
    """
    if not isinstance(email, str):
        raise EmailValidationError("Email must be a valid string.")

    cleaned = email.strip()
    if len(cleaned) < 5 or len(cleaned) > 254:
        raise EmailValidationError(
            f"Email address length must be between 5 and 254 characters (got {len(cleaned)})."
        )

    if not _EMAIL_REGEX.match(cleaned):
        raise EmailValidationError(f"Invalid email address syntax: '{cleaned}'.")

    local_part, domain_part = cleaned.rsplit("@", 1)
    if len(local_part) > 64:
        raise EmailValidationError(
            f"Email local-part exceeds maximum allowed length of 64 characters (got {len(local_part)})."
        )

    # Lowercase domain (RFC standard) and lowercase localpart for canonical uniqueness
    # preserving all existing dots and plus tags intact
    normalized = f"{local_part.lower()}@{domain_part.lower()}"
    return normalized
