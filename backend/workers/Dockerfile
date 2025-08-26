FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/workers/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules first
COPY backend/shared/ ./shared/

# Copy application code
COPY backend/workers/ ./

# Set Python path to include the current directory
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from enhanced_base_worker import EnhancedBaseWorker; print('Enhanced worker import successful')" || exit 1

# Run the enhanced worker
CMD ["python", "enhanced_runner.py"]
