"""DERA Connectors — Typed Connection Configuration & Credential Boundaries.

Defines immutable, strongly-typed connection configurations with strict engine-specific
validation, TLS controls, timeout parameters, and secret masking.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator

from dera_connectors.engine import DatabaseEngine


class TLSSettings(BaseModel):
    """Transport Layer Security configuration for remote database connections."""

    model_config = ConfigDict(frozen=True)

    ssl_mode: str = Field(
        default="prefer",
        description="TLS verification mode (disable, allow, prefer, require, verify-ca, verify-full).",
    )
    ca_cert_path: str | None = Field(
        default=None,
        description="Path to CA certificate authority file for TLS validation.",
    )
    client_cert_path: str | None = Field(
        default=None,
        description="Path to client certificate file for mutual TLS.",
    )
    client_key_path: str | None = Field(
        default=None,
        description="Path to client private key for mutual TLS.",
    )
    verify_hostname: bool = Field(
        default=True,
        description="Whether to verify server certificate hostname matching.",
    )


class TimeoutSettings(BaseModel):
    """Configurable timeout boundaries for connector operations."""

    model_config = ConfigDict(frozen=True)

    connect_timeout_seconds: float = Field(
        default=10.0,
        ge=0.5,
        le=120.0,
        description="Maximum seconds allowed to establish network connection.",
    )
    query_timeout_seconds: float = Field(
        default=30.0,
        ge=0.5,
        le=300.0,
        description="Maximum seconds allowed per individual metadata introspection query.",
    )
    total_deadline_seconds: float = Field(
        default=60.0,
        ge=1.0,
        le=600.0,
        description="Overall deadline for composite introspection operations.",
    )


class ConnectorConfig(BaseModel):
    """Typed connection configuration for database connector instances."""

    model_config = ConfigDict(frozen=True)

    engine: DatabaseEngine = Field(
        ...,
        description="Database engine type (postgresql, sqlite, mysql, mariadb).",
    )
    database: str = Field(
        ...,
        min_length=1,
        description="Database name, catalog identifier, or SQLite file path.",
    )
    host: str | None = Field(
        default=None,
        description="Hostname or IP address for network-attached databases.",
    )
    port: int | None = Field(
        default=None,
        ge=1,
        le=65535,
        description="Network port for database listener.",
    )
    username: str | None = Field(
        default=None,
        description="Database user identity for authentication.",
    )
    password: SecretStr | None = Field(
        default=None,
        description="Database password wrapped in SecretStr to prevent accidental exposure.",
    )
    credential_reference: str | None = Field(
        default=None,
        description="Vault secret reference or URI for dynamic server-side credential resolution.",
    )
    tls: TLSSettings = Field(
        default_factory=TLSSettings,
        description="TLS/SSL connection parameters.",
    )
    timeouts: TimeoutSettings = Field(
        default_factory=TimeoutSettings,
        description="Bounded timeout limits.",
    )
    driver_options: dict[str, Any] = Field(
        default_factory=dict,
        description="Engine-specific driver tuning options.",
    )

    @model_validator(mode="after")
    def validate_engine_configuration(self) -> "ConnectorConfig":
        """Validate engine-specific constraints."""
        if self.engine == DatabaseEngine.SQLITE:
            # SQLite does not use host, port, or remote TLS settings
            if self.host is not None:
                raise ValueError("Host must not be specified for SQLite connector.")
            if self.port is not None:
                raise ValueError("Port must not be specified for SQLite connector.")
        else:
            # Network engines require host
            if not self.host:
                raise ValueError(f"Host is required for {self.engine.value} connector.")
            # Set default ports if omitted
            if self.port is None:
                default_ports = {
                    DatabaseEngine.POSTGRESQL: 5432,
                    DatabaseEngine.MYSQL: 3306,
                    DatabaseEngine.MARIADB: 3306,
                }
                object.__setattr__(self, "port", default_ports.get(self.engine))

        return self

    def safe_dict(self) -> dict[str, Any]:
        """Return configuration dictionary with all credentials and sensitive tokens masked."""
        return {
            "engine": self.engine.value,
            "database": self.database,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "has_password": self.password is not None,
            "credential_reference": self.credential_reference,
            "tls": {
                "ssl_mode": self.tls.ssl_mode,
                "verify_hostname": self.tls.verify_hostname,
            },
            "timeouts": {
                "connect_timeout_seconds": self.timeouts.connect_timeout_seconds,
                "query_timeout_seconds": self.timeouts.query_timeout_seconds,
                "total_deadline_seconds": self.timeouts.total_deadline_seconds,
            },
        }

    def __repr__(self) -> str:
        safe = self.safe_dict()
        return f"ConnectorConfig({safe})"

    def __str__(self) -> str:
        return self.__repr__()
