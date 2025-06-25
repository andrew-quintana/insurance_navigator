# Multi-stage build for faster deployment
FROM python:3.11-slim as builder

# Create app user in builder stage and install as that user
RUN useradd --create-home --shell /bin/bash app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Add build arg to force cache invalidation
ARG CACHEBUST=1

# Copy requirements and install as app user
COPY config/python/requirements-prod.txt /tmp/requirements.txt
USER app
RUN pip install --upgrade pip --user && \
    pip install --no-cache-dir --user -r /tmp/requirements.txt && \
    pip install --no-cache-dir sentence-transformers==2.2.2 llama-parse==0.1.1

# Final stage - smaller image
FROM python:3.11-slim

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user in final stage
RUN useradd --create-home --shell /bin/bash app

# Copy pre-built dependencies with correct ownership from start
COPY --from=builder --chown=app:app /home/app/.local /home/app/.local

# Set working directory and copy app code
WORKDIR /app
COPY --chown=app:app . .

# Switch to app user
USER app

# Make sure Python scripts are available in PATH for app user
ENV PATH=/home/app/.local/bin:$PATH
ENV PYTHONPATH=/home/app/.local/lib/python3.11/site-packages:$PYTHONPATH

# Expose port and set environment variables
EXPOSE 8000
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV KEEP_ALIVE=75
ENV MAX_REQUESTS=1000
ENV MAX_REQUESTS_JITTER=100
ENV WORKERS=2

# Optimized health check with longer intervals for free tier
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use the app user's local bin path for uvicorn with optimized settings
CMD ["/home/app/.local/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "2", "--timeout-keep-alive", "75", "--limit-max-requests", "1000", \
     "--limit-max-requests-jitter", "100"]