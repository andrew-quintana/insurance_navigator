#!/bin/bash
# ========== START STAGING ENVIRONMENT ==========

set -e

# Set environment and load staging environment
export ENVIRONMENT=staging
export $(cat .env.staging | grep -v '^#' | xargs)

echo "🚀 Starting Staging Environment"
echo "==============================="

echo "📊 Environment: Staging"
echo "🏠 Frontend: https://staging.yourapp.com"
echo "🔧 Backend: https://api-staging.yourapp.com"
echo "🗄️  Database: Staging Supabase"
echo ""

# Start backend API
echo "1️⃣ Starting backend API..."
docker-compose -f docker-compose.staging.yml up -d api worker

# Wait for backend to be ready
echo "2️⃣ Waiting for backend to be ready..."
sleep 10
curl -f https://api-staging.yourapp.com/health > /dev/null 2>&1 || echo "⚠️  Backend not ready yet, continuing..."

echo ""
echo "✅ Staging environment started!"
echo "🌐 Frontend: https://staging.yourapp.com"
echo "🔧 Backend: https://api-staging.yourapp.com"
echo "🗄️  Database: Staging Supabase"
echo ""
echo "Press Ctrl+C to stop all services"