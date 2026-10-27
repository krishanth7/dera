"""Unit Tests for DERA MySQL and MariaDB Connector Configurations.

Validates:
- Engine type enforcement and validation
- Default port (3306) and charset (utf8mb4) bindings
- Credential masking and secret isolation
- Timeout and TLS bounds
"""

import unittest

from dera_connectors.configuration import TimeoutSettings, TLSSettings
from dera_connectors.engine import DatabaseEngine, DatabaseProvider
from dera_connectors.mariadb.configuration import MariaDbConnectorConfig
from dera_connectors.mysql.configuration import MySqlConnectorConfig
from pydantic import SecretStr


class TestMySqlAndMariaDbConfiguration(unittest.TestCase):
    """Test suite verifying MySQL and MariaDB typed connection configurations."""

    def test_mysql_configuration_defaults(self) -> None:
        """Verify MySqlConnectorConfig defaults to port 3306, utf8mb4, and MYSQL engine."""
        config = MySqlConnectorConfig(
            database="shop_db",
            host="db.example.com",
            username="analyst_readonly",
            password=SecretStr("SuperSecret123!"),
        )
        self.assertEqual(config.engine, DatabaseEngine.MYSQL)
        self.assertEqual(config.port, 3306)
        self.assertEqual(config.charset, "utf8mb4")
        self.assertEqual(config.provider, DatabaseProvider.GENERIC)
        self.assertNotIn("SuperSecret123!", repr(config))
        self.assertNotIn("SuperSecret123!", str(config))
        self.assertEqual(config.password.get_secret_value(), "SuperSecret123!")

    def test_mysql_configuration_custom_port_and_provider(self) -> None:
        """Verify custom port and cloud provider settings are preserved."""
        config = MySqlConnectorConfig(
            database="app_db",
            host="aurora-mysql.cluster-xyz.rds.amazonaws.com",
            port=3307,
            provider=DatabaseProvider.AWS_AURORA,
            timeouts=TimeoutSettings(connect_timeout_seconds=5.0, query_timeout_seconds=15.0),
        )
        self.assertEqual(config.port, 3307)
        self.assertEqual(config.provider, DatabaseProvider.AWS_AURORA)
        self.assertEqual(config.timeouts.connect_timeout_seconds, 5.0)

    def test_mariadb_configuration_defaults(self) -> None:
        """Verify MariaDbConnectorConfig defaults to port 3306, utf8mb4, and MARIADB engine."""
        config = MariaDbConnectorConfig(
            database="warehouse_db",
            host="mariadb.internal",
            username="reader",
            password=SecretStr("P@ssw0rdMaria!"),
        )
        self.assertEqual(config.engine, DatabaseEngine.MARIADB)
        self.assertEqual(config.port, 3306)
        self.assertEqual(config.charset, "utf8mb4")
        self.assertNotIn("P@ssw0rdMaria!", repr(config))

    def test_tls_settings_configuration(self) -> None:
        """Verify TLS settings configuration and certificate path bindings."""
        tls = TLSSettings(
            ssl_mode="verify-ca",
            ca_cert_path="/etc/ssl/certs/ca-bundle.pem",
            verify_hostname=True,
        )
        config = MySqlConnectorConfig(
            database="secure_db",
            host="db.secure.com",
            tls=tls,
        )
        self.assertEqual(config.tls.ssl_mode, "verify-ca")
        self.assertEqual(config.tls.ca_cert_path, "/etc/ssl/certs/ca-bundle.pem")
        self.assertTrue(config.tls.verify_hostname)
