"""DERA Application Backend Gateway Entry Point.

ASGI entrypoint exposing the authoritative FastAPI application instance
constructed deterministically by the application factory.
"""

import uvicorn

from dera_api.core.config import get_settings
from dera_api.factory import create_app

settings = get_settings()
app = create_app(settings)

if __name__ == "__main__":
    uvicorn.run(
        "dera_api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
