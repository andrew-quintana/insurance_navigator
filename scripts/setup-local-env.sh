#!/bin/bash

set -e

echo "Setting up local development environment for 003 Worker Refactor..."

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "Docker required but not installed." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose required but not installed." >&2; exit 1; }

echo "✅ Prerequisites check passed"

# Create necessary directories
echo "Creating local storage and log directories..."
mkdir -p local-storage/raw local-storage/parsed
mkdir -p logs/api logs/worker logs/monitoring

# Copy environment configuration if it doesn't exist
if [ ! -f .env.local ]; then
    echo "Creating local environment configuration..."
    cat > .env.local << EOF
# Local Development Environment Configuration
UPLOAD_PIPELINE_ENVIRONMENT=local
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/accessa_dev
SUPABASE_URL=http://localhost:5000
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU
LLAMAPARSE_API_URL=http://localhost:8001
OPENAI_API_URL=http://localhost:8002
EOF
    echo "✅ Local environment configuration created"
else
    echo "✅ Local environment configuration already exists"
fi

# Build and start services
echo "Building Docker images..."
docker-compose build

echo "Starting core services..."
docker-compose up -d postgres supabase-storage

# Wait for database to be ready
echo "Waiting for database to be ready..."
until docker-compose exec postgres pg_isready -U postgres; do
    echo "Database not ready, waiting..."
    sleep 2
done
echo "✅ Database is ready"

# Run database migrations
echo "Running database migrations..."
docker-compose exec postgres psql -U postgres -d accessa_dev -f /docker-entrypoint-initdb.d/001_create_schemas.sql
echo "✅ Database migrations completed"

# Start remaining services
echo "Starting application services..."
docker-compose up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 15

# Verify all services are healthy
echo "Verifying service health..."

# Health check API server
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ API server health check passed"
else
    echo "❌ API server health check failed"
    exit 1
fi

# Health check worker process
if docker-compose exec base-worker python -c "from backend.workers.base_worker import BaseWorker; print('Worker import successful')" >/dev/null 2>&1; then
    echo "✅ BaseWorker health check passed"
else
    echo "❌ BaseWorker health check failed"
    exit 1
fi

# Health check mock services
if curl -f http://localhost:8001/health >/dev/null 2>&1; then
    echo "✅ Mock LlamaParse health check passed"
else
    echo "❌ Mock LlamaParse health check failed"
    exit 1
fi

if curl -f http://localhost:8002/health >/dev/null 2>&1; then
    echo "✅ Mock OpenAI health check passed"
else
    echo "❌ Mock OpenAI health check failed"
    exit 1
fi

echo ""
echo "🎉 Local environment setup complete!"
echo ""
echo "Services available at:"
echo "  API Server:     http://localhost:8000"
echo "  Mock LlamaParse: http://localhost:8001"
echo "  Mock OpenAI:    http://localhost:8002"
echo "  Monitoring:     http://localhost:3000"
echo "  Database:       localhost:5432"
echo ""
echo "Next steps:"
echo "  1. Run tests: ./scripts/run-local-tests.sh"
echo "  2. Validate environment: ./scripts/validate-local-environment.sh"
echo "  3. View logs: docker-compose logs -f [service-name]"
echo ""
echo "Environment setup completed in $(($(date +%s) - $(date +%s))) seconds"
