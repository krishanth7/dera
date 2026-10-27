"""Tests for RFC 9457 Problem Details error contracts and taxonomy (Phase 4.2)."""

from __future__ import annotations

import unittest

from dera_api.contracts.errors import (
    PROBLEM_JSON_MEDIA_TYPE,
    ErrorCode,
    FieldErrorDetail,
    ProblemDetail,
)
from dera_api.core.exceptions import (
    ConflictError,
    DependencyUnavailableError,
    DeraError,
    ResourceNotFoundError,
    ValidationDomainError,
    register_exception_handlers,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestErrorContracts(unittest.TestCase):
    """Validate RFC 9457 Problem Details model, media type, and domain exception mapping."""

    def test_error_code_taxonomy_completeness(self) -> None:
        """Verify all canonical error codes exist in ErrorCode enum."""
        expected_codes = {
            "VALIDATION_ERROR",
            "MALFORMED_REQUEST",
            "UNSUPPORTED_MEDIA_TYPE",
            "RESOURCE_NOT_FOUND",
            "METHOD_NOT_ALLOWED",
            "CONFLICT",
            "RATE_LIMITED",
            "INTERNAL_ERROR",
            "SERVICE_UNAVAILABLE",
            "DEPENDENCY_UNAVAILABLE",
        }
        actual_codes = {code.value for code in ErrorCode}
        self.assertTrue(expected_codes.issubset(actual_codes))

    def test_field_error_detail_model(self) -> None:
        """Verify FieldErrorDetail serialization."""
        field_err = FieldErrorDetail(
            field="page_size",
            code="VALUE_TOO_LARGE",
            message="page_size must not exceed 100",
            constraint="le=100",
        )
        data = field_err.model_dump()
        self.assertEqual(data["field"], "page_size")
        self.assertEqual(data["code"], "VALUE_TOO_LARGE")
        self.assertEqual(data["message"], "page_size must not exceed 100")
        self.assertEqual(data["constraint"], "le=100")

    def test_problem_detail_rfc9457_structure(self) -> None:
        """Verify ProblemDetail serializes standard RFC 9457 attributes."""
        problem = ProblemDetail(
            type="https://api.dera.io/v1/errors/VALIDATION_ERROR",
            title="Validation Failed",
            status=422,
            detail="Request validation failed for 1 field.",
            instance="/api/v1/catalogs",
            code=ErrorCode.VALIDATION_ERROR,
            request_id="req-test-uuid",
            errors=[
                FieldErrorDetail(
                    field="name",
                    code="STRING_TOO_SHORT",
                    message="At least 2 characters required",
                )
            ],
            error={"code": "VALIDATION_ERROR", "request_id": "req-test-uuid"},
        )

        dump = problem.model_dump()
        self.assertEqual(dump["type"], "https://api.dera.io/v1/errors/VALIDATION_ERROR")
        self.assertEqual(dump["title"], "Validation Failed")
        self.assertEqual(dump["status"], 422)
        self.assertEqual(dump["detail"], "Request validation failed for 1 field.")
        self.assertEqual(dump["instance"], "/api/v1/catalogs")
        self.assertEqual(dump["code"], "VALIDATION_ERROR")
        self.assertEqual(dump["request_id"], "req-test-uuid")
        self.assertEqual(len(dump["errors"]), 1)
        self.assertEqual(dump["errors"][0]["field"], "name")

        # Verify backward compatibility error envelope
        self.assertEqual(dump["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(dump["error"]["request_id"], "req-test-uuid")

    def test_domain_exception_hierarchy(self) -> None:
        """Verify domain exception inheritance and safe attribute storage."""
        base_err = DeraError("Base error", code=ErrorCode.INTERNAL_ERROR)
        self.assertEqual(base_err.status_code, 400)
        self.assertEqual(base_err.code, ErrorCode.INTERNAL_ERROR)

        not_found = ResourceNotFoundError(
            "Schema 'public' not found",
            resource_type="schema",
            resource_id="public",
        )
        self.assertEqual(not_found.status_code, 404)
        self.assertEqual(not_found.code, ErrorCode.RESOURCE_NOT_FOUND)
        self.assertEqual(not_found.details["resource_type"], "schema")

        conflict = ConflictError("Table 'orders' already exists")
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.code, ErrorCode.CONFLICT)

        dep_err = DependencyUnavailableError("PostgreSQL pool connection timeout")
        self.assertEqual(dep_err.status_code, 503)
        self.assertEqual(dep_err.code, ErrorCode.DEPENDENCY_UNAVAILABLE)

        val_err = ValidationDomainError("Invalid catalog configuration")
        self.assertEqual(val_err.status_code, 422)
        self.assertEqual(val_err.code, ErrorCode.VALIDATION_ERROR)


class TestExceptionHandlingIntegration(unittest.TestCase):
    """Integration test verifying exception handlers return RFC 9457 responses."""

    def setUp(self) -> None:
        self.app = FastAPI()
        register_exception_handlers(self.app)

        @self.app.get("/trigger/not-found")
        def route_not_found() -> None:
            raise ResourceNotFoundError("Database catalog 'demo' not found.")

        @self.app.get("/trigger/conflict")
        def route_conflict() -> None:
            raise ConflictError("Version conflict: resource modified.")

        @self.app.get("/trigger/dependency-unavailable")
        def route_dependency() -> None:
            raise DependencyUnavailableError("Storage engine unresponsive.")

        @self.app.get("/trigger/unhandled")
        def route_unhandled() -> None:
            raise RuntimeError("Unexpected zero-division or memory fault")

        self.client = TestClient(self.app, raise_server_exceptions=False)

    def test_not_found_handler(self) -> None:
        response = self.client.get("/trigger/not-found")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers["content-type"], PROBLEM_JSON_MEDIA_TYPE)
        data = response.json()
        self.assertEqual(data["code"], "RESOURCE_NOT_FOUND")
        self.assertEqual(data["title"], "Resource Not Found")
        self.assertIn("demo", data["detail"])

    def test_conflict_handler(self) -> None:
        response = self.client.get("/trigger/conflict")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.headers["content-type"], PROBLEM_JSON_MEDIA_TYPE)
        data = response.json()
        self.assertEqual(data["code"], "CONFLICT")
        self.assertEqual(data["title"], "Conflict")

    def test_dependency_unavailable_handler(self) -> None:
        response = self.client.get("/trigger/dependency-unavailable")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers["content-type"], PROBLEM_JSON_MEDIA_TYPE)
        data = response.json()
        self.assertEqual(data["code"], "DEPENDENCY_UNAVAILABLE")
        self.assertEqual(data["status"], 503)

    def test_unhandled_exception_sanitizes_stack_trace(self) -> None:
        response = self.client.get("/trigger/unhandled")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.headers["content-type"], PROBLEM_JSON_MEDIA_TYPE)
        data = response.json()
        self.assertEqual(data["code"], "INTERNAL_ERROR")
        self.assertEqual(data["title"], "Internal Server Error")
        self.assertNotIn("Unexpected zero-division", data["detail"])
        self.assertNotIn("traceback", data)
