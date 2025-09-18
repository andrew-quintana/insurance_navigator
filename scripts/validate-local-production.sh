#!/bin/bash
# Validate local environment matches production

echo "🔍 Validating local environment matches production..."

# Load production environment variables
if [ -f .env.production ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
    echo "✅ Loaded production environment variables"
else
    echo "❌ .env.production not found"
    exit 1
fi

# Check Docker images
echo "Checking Docker images..."
docker images | grep insurance-navigator

# Check container health
echo "Checking container health..."
docker-compose ps

# Check environment variables
echo "Checking environment variables..."
docker-compose exec api env | grep -E "(SUPABASE|ENVIRONMENT)" || echo "⚠️  No containers running"

# Check Python path
echo "Checking Python path..."
docker-compose exec api python -c "import sys; print('Python path:', sys.path)" || echo "⚠️  No containers running"

# Test module imports
echo "Testing module imports..."
docker-compose exec api python -c "from api.upload_pipeline.webhooks import router; print('✅ API imports successful')" || echo "❌ API imports failed"
docker-compose exec worker python -c "from backend.workers.enhanced_base_worker import EnhancedBaseWorker; print('✅ Worker imports successful')" || echo "❌ Worker imports failed"

# Test health endpoints
echo "Testing health endpoints..."
curl -f http://localhost:8000/health || echo "❌ API health check failed"
curl -f http://localhost:3000 || echo "❌ Frontend health check failed"

echo "✅ Local environment validation completed!"
