"""DERA Connectors — Unified Connector Security Policy.

Acts as the primary server-side security gateway orchestrating authorization,
destination validation, read-only enforcement, query allowlists, timeout budgets,
resource bounds, and audit logging across all database connector adapters.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Sequence
from typing import Any

from dera_connectors.context import ConnectorContext
from dera_connectors.security.audit import log_security_audit_event
from dera_connectors.security.authorization import validate_workspace_authorization
from dera_connectors.security.destinations import validate_network_target
from dera_connectors.security.errors import (
    ConnectorSecurityError,
    SSRFSecurityViolationError,
    TenantIsolationViolationError,
)
from dera_connectors.security.isolation import validate_filesystem_target
from dera_connectors.security.query_policy import (
    GLOBAL_QUERY_REGISTRY,
    ApprovedMetadataQueryRegistry,
    QuerySpecification,
)
from dera_connectors.security.resource_limits import ConnectorResourceLimits
from dera_connectors.security.timeouts import DeadlineTracker, TimeoutBudget


class ConnectorSecurityPolicy:
    """Unified server-side connector security policy manager."""

    def __init__(
        self,
        query_registry: ApprovedMetadataQueryRegistry | None = None,
        timeout_budget: TimeoutBudget | None = None,
        resource_limits: ConnectorResourceLimits | None = None,
        allow_private_networks: bool = False,
        allow_loopback: bool = False,
    ) -> None:
        self.query_registry = query_registry or GLOBAL_QUERY_REGISTRY
        self.timeout_budget = timeout_budget or TimeoutBudget()
        self.resource_limits = resource_limits or ConnectorResourceLimits()
        self.allow_private_networks = allow_private_networks
        self.allow_loopback = allow_loopback

    def evaluate_connection_target(
        self,
        context: ConnectorContext,
        engine: str,
        host: str | None = None,
        port: int | None = None,
        db_path: str | None = None,
        approved_roots: Sequence[str] | None = None,
        target_workspace_id: uuid.UUID | str | None = None,
    ) -> None:
        """Validate an intended database connection request against all security invariants.

        Parameters
        ----------
        context : ConnectorContext
            Active connector execution context.
        engine : str
            Target engine name ('postgresql', 'sqlite', 'mysql', 'mariadb').
        host : str | None
            Remote database hostname or IP.
        port : int | None
            Remote database TCP port.
        db_path : str | None
            Local SQLite file path if applicable.
        approved_roots : Sequence[str] | None
            Approved filesystem directories for SQLite.
        target_workspace_id : uuid.UUID | str | None
            Workspace that owns the connection configuration.

        Raises
        ------
        TenantIsolationViolationError
            If caller workspace does not match target workspace.
        SSRFSecurityViolationError
            If network target violates SSRF boundaries.
        FilesystemIsolationViolationError
            If local filesystem path violates storage isolation.
        """
        start = time.monotonic()
        operation = f"{engine}.connect"

        # 1. Workspace isolation verification
        if target_workspace_id is not None:
            try:
                validate_workspace_authorization(context.workspace_id, target_workspace_id)
            except TenantIsolationViolationError as exc:
                log_security_audit_event(
                    workspace_id=str(context.workspace_id),
                    engine=engine,
                    operation_id=operation,
                    status="VIOLATION",
                    duration_ms=(time.monotonic() - start) * 1000.0,
                    details={"violation": str(exc)},
                )
                raise

        # 2. Filesystem checks for SQLite
        if engine.lower() == "sqlite" and db_path:
            try:
                validate_filesystem_target(
                    db_path=db_path,
                    approved_roots=approved_roots,
                    allow_memory=False,
                    workspace_id=str(context.workspace_id),
                )
            except Exception as exc:
                log_security_audit_event(
                    workspace_id=str(context.workspace_id),
                    engine=engine,
                    operation_id=operation,
                    status="VIOLATION",
                    duration_ms=(time.monotonic() - start) * 1000.0,
                    details={"path": db_path, "violation": str(exc)},
                )
                raise

        # 3. Network egress & SSRF checks for network engines
        if host:
            try:
                validate_network_target(
                    host=host,
                    allow_private_networks=self.allow_private_networks,
                    allow_loopback=self.allow_loopback,
                    port=port,
                )
            except SSRFSecurityViolationError as exc:
                log_security_audit_event(
                    workspace_id=str(context.workspace_id),
                    engine=engine,
                    operation_id=operation,
                    status="VIOLATION",
                    duration_ms=(time.monotonic() - start) * 1000.0,
                    details={"host": host, "port": port, "violation": str(exc)},
                )
                raise

        log_security_audit_event(
            workspace_id=str(context.workspace_id),
            engine=engine,
            operation_id=operation,
            status="ALLOW",
            duration_ms=(time.monotonic() - start) * 1000.0,
            details={"host": host, "port": port, "db_path": db_path},
        )

    def evaluate_query(
        self,
        context: ConnectorContext,
        engine: str,
        operation_id: str,
        sql: str,
        parameters: dict[str, Any] | None = None,
    ) -> QuerySpecification:
        """Validate an intended SQL query before driver execution.

        Parameters
        ----------
        context : ConnectorContext
            Active execution context.
        engine : str
            Database engine.
        operation_id : str
            Operation identifier from the query registry.
        sql : str
            SQL query string.
        parameters : dict[str, Any] | None
            Query parameters.

        Returns
        -------
        QuerySpecification
            Approved query specification.

        Raises
        ------
        ReadOnlySecurityViolationError
            If query attempts schema or data mutation.
        UnauthorizedQueryError
            If query is not allowed for engine or violates query policy.
        """
        start = time.monotonic()

        # Check active context state
        context.check_active()

        try:
            spec = self.query_registry.validate_operation(
                operation_id=operation_id,
                engine=engine,
                sql=sql,
                parameters=parameters,
            )
            log_security_audit_event(
                workspace_id=str(context.workspace_id),
                engine=engine,
                operation_id=operation_id,
                status="ALLOW",
                duration_ms=(time.monotonic() - start) * 1000.0,
            )
            return spec
        except ConnectorSecurityError as exc:
            log_security_audit_event(
                workspace_id=str(context.workspace_id),
                engine=engine,
                operation_id=operation_id,
                status="VIOLATION",
                duration_ms=(time.monotonic() - start) * 1000.0,
                details={"violation": str(exc)},
            )
            raise

    def create_deadline_tracker(
        self,
        deadline_seconds: float | None = None,
        operation_name: str = "inspection",
    ) -> DeadlineTracker:
        """Create a monotonic deadline tracker bound to configured timeout limits."""
        deadline = (
            deadline_seconds
            if deadline_seconds is not None
            else self.timeout_budget.overall_inspection_deadline_seconds
        )
        return DeadlineTracker(deadline_seconds=deadline, operation_name=operation_name)
