#!/bin/bash
# Pre-deployment testing script

echo "🔍 Running pre-deployment tests..."

# Load production environment variables
if [ -f .env.production ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
    echo "✅ Loaded production environment variables"
else
    echo "❌ .env.production not found"
    exit 1
fi

# 1. Test Docker builds locally
echo "1. Testing Docker builds..."
docker-compose build --no-cache

# 2. Test module imports
echo "2. Testing module imports..."
docker-compose run --rm api python -c "import api; import backend; print('✅ All imports successful')"

# 3. Test dependency resolution
echo "3. Testing dependency resolution..."
docker-compose run --rm api pip check

# 4. Test health checks
echo "4. Testing health checks..."
docker-compose up -d
sleep 30
curl -f http://localhost:8000/health || echo "❌ Health check failed"
docker-compose down

echo "✅ Pre-deployment tests completed!"
