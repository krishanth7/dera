# MySQL Version Compatibility Matrix

## Supported Engine Releases

The DERA MySQL Connector targets modern MySQL database engine releases with verifiable integration test coverage:

| Engine Version | Release Type | Support Status | Key Behavioral Characteristics |
|---|---|---|---|
| **MySQL 8.4 LTS** | Long-Term Support | Supported | Native `CHECK_CONSTRAINTS`, functional indexes, default `caching_sha2_password` authentication, strict SQL modes. |
| **MySQL 8.0.x** | General Availability | Supported | MySQL 8.0.16+ supports `CHECK_CONSTRAINTS`; 8.0.13+ supports functional expression indexes; default `utf8mb4_0900_ai_ci` collation. |
| **MySQL 5.7** | End of Life (Oct 2023) | Restricted / Legacy | Lacks `CHECK_CONSTRAINTS` in `INFORMATION_SCHEMA`; lacks functional indexes; legacy query timeout variable syntax. |

---

## Dialect and Driver Compatibility

- **Driver:** `PyMySQL` (>=1.1.0) pure Python driver.
- **Python Runtimes:** Python 3.12, 3.13.
- **TLS Protocols:** TLS 1.2, TLS 1.3 enforced by `ssl.SSLContext`.
- **Operating Systems:** Linux (Ubuntu 22.04+), macOS (13+), Windows 10/11 / Windows Server 2022.
- **Authentication Plugins:** `mysql_native_password`, `caching_sha2_password`.

---

## Unsupported Configurations

- Plaintext network transport in multi-tenant cloud environments (`ssl_mode='disable'` rejected in production).
- MySQL 5.5 and older releases lacking modern `INFORMATION_SCHEMA` metadata structures.
- User accounts requiring administrative `SUPER`, `PROCESS`, or `RELOAD` privileges.
