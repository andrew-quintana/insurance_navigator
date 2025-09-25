#!/bin/bash
# ========== START PRODUCTION ENVIRONMENT ==========

set -e

# Set environment and load production environment
export ENVIRONMENT=production
export $(cat .env.production | grep -v '^#' | xargs)

echo "🚀 Starting Production Environment"
echo "================================="

echo "📊 Environment: Production"
echo "🏠 Frontend: https://yourapp.com"
echo "🔧 Backend: https://api.yourapp.com"
echo "🗄️  Database: Production Supabase"
echo ""

# Start backend API
echo "1️⃣ Starting backend API..."
docker-compose -f docker-compose.production.yml up -d api worker

# Wait for backend to be ready
echo "2️⃣ Waiting for backend to be ready..."
sleep 10
curl -f https://api.yourapp.com/health > /dev/null 2>&1 || echo "⚠️  Backend not ready yet, continuing..."

echo ""
echo "✅ Production environment started!"
echo "🌐 Frontend: https://yourapp.com"
echo "🔧 Backend: https://api.yourapp.com"
echo "🗄️  Database: Production Supabase"
echo ""
echo "Press Ctrl+C to stop all services"