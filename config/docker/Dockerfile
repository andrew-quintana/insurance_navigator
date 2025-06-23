# Multi-stage build for faster deployment
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY config/python/requirements-prod.txt requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# Final stage - smaller image
FROM python:3.11-slim

# Install only runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user first
RUN useradd --create-home --shell /bin/bash app

# Copy pre-built dependencies from builder stage to app user's home
COPY --from=builder /root/.local /home/app/.local
RUN chown -R app:app /home/app/.local

# Set working directory and copy app code
WORKDIR /app
COPY . .
RUN chown -R app:app /app

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

# Optimized health check with shorter intervals
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=2 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use the app user's local bin path for uvicorn
CMD ["/home/app/.local/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"] 