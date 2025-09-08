# Multi-stage build for faster deployment
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install Python dependencies with robust error handling
COPY config/python/requirements-prod.txt /tmp/requirements.txt

# Install pip with retry and timeout configurations
RUN pip install --upgrade pip --timeout=300 --retries=5

# Install requirements with multiple retry strategies
RUN pip install --no-cache-dir \
    --timeout=300 \
    --retries=5 \
    -r /tmp/requirements.txt || \
    (echo "First attempt failed, retrying with different strategy..." && \
     sleep 5 && \
     pip install --no-cache-dir \
     --timeout=600 \
     --retries=3 \
     -r /tmp/requirements.txt)

# Final stage - smaller image
FROM python:3.11-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy all necessary application files
COPY main.py .
COPY config/ ./config/
COPY db/ ./db/
COPY backend/ ./backend/
COPY shared/ ./shared/
COPY utils/ ./utils/
COPY agents/ ./agents/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port and set environment variables
EXPOSE 8000
ENV PORT=8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Optimized health check with shorter intervals
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=2 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use uvicorn directly
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"] 