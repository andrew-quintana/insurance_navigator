FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install fastapi uvicorn

# Copy the mock storage service
COPY storage_server.py .

# Expose port
EXPOSE 5001

# Run the service
CMD ["python", "-m", "uvicorn", "storage_server:app", "--host", "0.0.0.0", "--port", "5001"]
