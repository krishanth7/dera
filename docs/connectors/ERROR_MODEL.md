# Connector Error Model & Exception Taxonomy

## Exception Hierarchy

All connector exceptions derive from `ConnectorError` (`packages/connectors/src/dera_connectors/errors.py`):

| Exception | Error Code | Description |
|---|---|---|
| `ConnectorUnavailableError` | `CONNECTOR_UNAVAILABLE` | Database server is unreachable or offline. |
| `ConnectorAuthenticationFailedError` | `CONNECTOR_AUTHENTICATION_FAILED` | Credentials rejected by database. |
| `ConnectorPermissionDeniedError` | `CONNECTOR_PERMISSION_DENIED` | Credentials lack required catalog read permissions. |
| `ConnectorTimeoutError` | `CONNECTOR_TIMEOUT` | Connection or query exceeded configured timeout limits. |
| `ConnectorTLSError` | `CONNECTOR_TLS_ERROR` | TLS handshake or certificate validation failed. |
| `ConnectorUnsupportedEngineError` | `CONNECTOR_UNSUPPORTED_ENGINE` | Unregistered database engine requested. |
| `ConnectorUnsupportedCapabilityError` | `CONNECTOR_UNSUPPORTED_CAPABILITY` | Introspection operation unsupported by this engine. |
| `ConnectorInvalidConfigurationError` | `CONNECTOR_INVALID_CONFIGURATION` | Malformed configuration provided. |
| `ConnectorConnectionLostError` | `CONNECTOR_CONNECTION_LOST` | Active connection dropped during operation. |
| `ConnectorMetadataError` | `CONNECTOR_METADATA_ERROR` | Catalog metadata corrupted or failed parsing. |
| `ConnectorCancelledError` | `CONNECTOR_CANCELLED` | Operation cancelled cooperatively by caller. |
| `ConnectorSecurityViolationError` | `CONNECTOR_SECURITY_VIOLATION` | Operation rejected by read-only or SSRF security policies. |

## Sanitization Guarantee

`ConnectorError.__init__` automatically scrubs raw connection strings, usernames, and passwords from exception messages using `mask_sensitive_strings`.
