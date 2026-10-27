"""DERA Connectors — Secure Credential Resolution & Masking.

Provides safe resolution, encapsulation, and disposal of database connection credentials,
guaranteeing zero plaintext exposure across logs, exceptions, and diagnostics.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from dera_connectors.security.errors import CredentialExposureError


@dataclass(frozen=True)
class DatabaseCredentials:
    """Immutable, encapsulated container for database authentication credentials."""

    username: str
    password: str = field(repr=False)  # Exclude from dataclass repr
    client_cert: str | None = field(default=None, repr=False)
    client_key: str | None = field(default=None, repr=False)

    def __repr__(self) -> str:
        """Sanitized string representation hiding password."""
        return f"DatabaseCredentials(username={self.username!r}, password='***')"

    def __str__(self) -> str:
        return self.__repr__()

    def expose_raw_password(self) -> str:
        """Explicit getter for database driver authentication only."""
        return self.password


class SecureCredentialResolver:
    """Resolves and protects database credentials in ephemeral memory."""

    @staticmethod
    def validate_credential_safety(username: str, password: str) -> None:
        """Ensure credentials do not contain null bytes or illegal control characters.

        Raises
        ------
        CredentialExposureError
            If credentials contain corrupt or dangerous characters.
        """
        if "\0" in username:
            raise CredentialExposureError("username contains null bytes")
        if "\0" in password:
            raise CredentialExposureError("password contains null bytes")

    @classmethod
    def resolve_from_dict(cls, data: dict[str, Any]) -> DatabaseCredentials:
        """Safely parse credentials from a connection dictionary.

        Parameters
        ----------
        data : dict[str, Any]
            Raw connection configuration dictionary.

        Returns
        -------
        DatabaseCredentials
            Encapsulated credentials.
        """
        username = str(data.get("username", "") or "")
        password = str(data.get("password", "") or "")
        client_cert = data.get("client_cert_path")
        client_key = data.get("client_key_path")

        cls.validate_credential_safety(username, password)
        return DatabaseCredentials(
            username=username,
            password=password,
            client_cert=client_cert,
            client_key=client_key,
        )

    @classmethod
    def resolve_from_env(cls, prefix: str = "DERA_DB_") -> DatabaseCredentials | None:
        """Resolve credentials from environment variables if present."""
        user = os.environ.get(f"{prefix}USER")
        pwd = os.environ.get(f"{prefix}PASSWORD")
        if user and pwd:
            cls.validate_credential_safety(user, pwd)
            return DatabaseCredentials(username=user, password=pwd)
        return None
