# Multi-stage build for faster deployment
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies with caching
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Final stage - smaller image
FROM python:3.11-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy pre-built dependencies
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the entire backend directory structure to maintain imports
COPY backend/ ./backend/
COPY core/ ./core/
COPY utils/ ./utils/

# Remove any conflicting config files that might be imported from the main API
RUN rm -rf ./config/ 2>/dev/null || true

# Set Python path to include the current directory
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Optimized health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=2 \
    CMD python -c "from backend.workers.enhanced_base_worker import EnhancedBaseWorker; print('Enhanced worker import successful')" || exit 1

# Run the enhanced worker from the workers directory
CMD ["python", "backend/workers/enhanced_runner.py"]
