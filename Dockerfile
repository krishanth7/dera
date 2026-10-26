# ============================================================
# DERA — Database Engineering & Reverse Analysis
# Enterprise Multi-Stage Container Image
#
# Principles:
#   - Deterministic builds
#   - Non-root execution (UID 10001)
#   - Minimal attack surface (distroless / slim base)
#   - Healthcheck endpoint verification
#   - Zero external AI services
# ============================================================

# Stage 1: Builder
FROM python:3.13-slim AS builder

WORKDIR /build

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY packages/core/ packages/core/
COPY apps/api/ apps/api/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --prefix=/install .

# Stage 2: Production Runtime
FROM python:3.13-slim AS runner

WORKDIR /app

# Create non-root system group and user
RUN groupadd -g 10001 dera && \
    useradd -u 10001 -g dera -s /bin/false -m -d /app dera

# Copy installed Python packages from builder
COPY --from=builder --chown=dera:dera /install /usr/local
COPY --chown=dera:dera apps/api/src/dera_api apps/api/src/dera_api
COPY --chown=dera:dera packages/core/src/dera packages/core/src/dera

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/packages/core/src:/app/apps/api/src \
    PORT=8000

USER dera:dera

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["python", "-m", "fastapi", "run", "apps/api/src/dera_api/main.py", "--host", "0.0.0.0", "--port", "8000"]
