FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy monitoring files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    psycopg2-binary \
    aiohttp \
    python-multipart

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Run the monitoring service
CMD ["python", "-m", "uvicorn", "production_monitoring:app", "--host", "0.0.0.0", "--port", "3000"]
