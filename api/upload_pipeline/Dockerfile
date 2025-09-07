# Optimized Dockerfile for API Service Only
# Multi-stage build for faster deployment and smaller image size

FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only API requirements
COPY api/upload_pipeline/requirements.txt /tmp/requirements.txt

# Install Python dependencies with caching
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Final stage - minimal runtime image
FROM python:3.11-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy only the API service code
COPY api/upload_pipeline/ ./api/upload_pipeline/
COPY config/ ./config/

# Copy pre-built dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Set environment variables
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Enhanced health check with better logging
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || (echo "Health check failed" && exit 1)

# Start command with enhanced logging
CMD ["python", "-m", "uvicorn", "api.upload_pipeline.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-level", "info", "--access-log"]