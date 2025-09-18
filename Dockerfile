# Multi-stage build for faster deployment
FROM python:3.11-slim as builder

# Install system dependencies with optimized layer
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user in builder stage
RUN useradd --create-home --shell /bin/bash app

# Set working directory and PATH
WORKDIR /app
ENV PATH=/home/app/.local/bin:$PATH
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Copy and install requirements as separate layer for better caching
COPY --chown=app:app config/python/requirements-prod.txt /tmp/requirements.txt
USER app
RUN --mount=type=cache,target=/home/app/.cache/pip,sharing=locked \
    pip install --user --no-warn-script-location -r /tmp/requirements.txt

# Final stage - smaller image
FROM python:3.11-slim

# Install runtime dependencies with optimized layer
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user and set up environment
RUN useradd --create-home --shell /bin/bash app
WORKDIR /app

# Copy pre-built dependencies and app code
COPY --from=builder --chown=app:app /home/app/.local /home/app/.local
COPY --chown=app:app . .

# Set up environment variables
ENV PATH=/home/app/.local/bin:$PATH
ENV PYTHONPATH=/home/app/.local/lib/python3.11/site-packages:$PYTHONPATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000
ENV KEEP_ALIVE=75
ENV MAX_REQUESTS=1000
ENV MAX_REQUESTS_JITTER=100
ENV WORKERS=1

# Switch to app user
USER app

# Expose port and configure health check
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start uvicorn with optimized settings
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "1", "--timeout-keep-alive", "75", "--limit-max-requests", "1000", \
     "--limit-max-requests-jitter", "100"]
