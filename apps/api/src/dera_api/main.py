"""DERA Application Backend Gateway.

FastAPI entrypoint providing health verification, version info,
and read-only database inspection endpoints.
"""

from fastapi import FastAPI
import dera

app = FastAPI(
    title="DERA API",
    description="Deterministic Database Engineering & Reverse Analysis Platform API",
    version=dera.__version__,
)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Returns the service health status."""
    return {"status": "healthy", "service": "dera-api", "version": dera.__version__}


@app.get("/info")
def platform_info() -> dict[str, str]:
    """Returns official platform identity and deterministic engineering principles."""
    return {
        "project": "DERA",
        "name": "Database Engineering & Reverse Analysis",
        "tagline": "Understand Every Schema. Engineer Every Change.",
        "maintainer": "Bunga Krishanth",
        "philosophy": "Deterministic, non-AI database reverse engineering",
        "version": dera.__version__,
    }
