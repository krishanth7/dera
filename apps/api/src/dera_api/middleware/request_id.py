"""DERA API — Request ID Correlation Middleware.

Generates or validates incoming correlation identifiers (X-Request-ID),
attaches them to request state, and returns them in the response headers.
"""

import re
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

VALID_REQUEST_ID_REGEX = re.compile(r"^[A-Za-z0-9\-_]{1,128}$")


def is_valid_request_id(request_id: str | None) -> bool:
    """Validates whether a client-provided correlation ID is safe and bounded."""
    if not request_id:
        return False
    return bool(VALID_REQUEST_ID_REGEX.match(request_id))


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing request ID generation, validation, and propagation."""

    def __init__(self, app: Callable, header_name: str = "X-Request-ID") -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        incoming_id = request.headers.get(self.header_name)
        if incoming_id and is_valid_request_id(incoming_id):
            request_id = incoming_id
        else:
            request_id = uuid.uuid4().hex

        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[self.header_name] = request_id
        return response
