#!/bin/bash
# Test Docker build and run with Render-like environment

echo "🐳 Testing Docker Build with Render Environment"
echo "=============================================="

# Build the Docker image
echo "📦 Building Docker image..."
docker build -t insurance-navigator-test .

# Run with Render-like environment variables
echo "🚀 Running with Render environment variables..."
docker run --rm -p 10000:10000 \
  -e PORT=10000 \
  -e API_HOST=0.0.0.0 \
  -e API_PORT=8000 \
  -e ENVIRONMENT=staging \
  insurance-navigator-test &

# Wait for startup
echo "⏳ Waiting for application to start..."
sleep 15

# Test health endpoint
echo "🔍 Testing health endpoint..."
curl -s http://localhost:10000/health | jq . || echo "Health check failed"

# Clean up
echo "🛑 Stopping Docker container..."
docker stop $(docker ps -q --filter ancestor=insurance-navigator-test)
