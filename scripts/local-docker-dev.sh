#!/bin/bash
# Local Docker development script

echo "🐳 Starting local Docker development environment..."

# Load production environment variables
if [ -f .env.production ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
    echo "✅ Loaded production environment variables"
else
    echo "❌ .env.production not found"
    exit 1
fi

# Build and start services
echo "Building and starting services..."
docker-compose up --build

echo "🚀 Local development environment started!"
echo "API: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Worker: Running in background"
