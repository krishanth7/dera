# Credential Handling & Secret Boundaries

## Secret Isolation

1. **`SecretStr` Encapsulation:** Passwords in `ConnectorConfig` are stored as Pydantic `SecretStr`. They cannot be printed in logs, serialized in API responses, or exposed via `str()` / `repr()`.
2. **Safe Serialization (`safe_dict()`):** Provides sanitized configuration dictionaries for logging and API status reporting (`has_password: true`, no cleartext).
3. **Vault Reference Resolution:** Configurations support `credential_reference`, allowing database credentials to be dynamically resolved from KMS or server-side secret vaults rather than stored in plain text.
4. **Log Scrubber:** `mask_sensitive_strings` automatically redacts database connection URIs (`postgres://user:***@host/db`) and password key-values before writing to logs or error messages.
