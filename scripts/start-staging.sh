#!/bin/bash
# ========== START STAGING ENVIRONMENT ==========
# Structural tool for starting staging environment
# This script should remain stable and isolated from project updates

set -e

# Set environment and load staging environment
export ENVIRONMENT=staging

# Check if staging environment file exists
if [ ! -f ".env.staging" ]; then
    echo "❌ Staging environment file (.env.staging) not found!"
    echo "Please ensure the staging environment is properly configured."
    exit 1
fi

# Load staging environment variables
export $(cat .env.staging | grep -v '^#' | xargs)

echo "🚀 Starting Staging Environment"
echo "==============================="

# Get actual URLs from environment variables
FRONTEND_URL="${NEXT_PUBLIC_APP_URL:-https://insurance-navigator.vercel.app}"
API_URL="${NEXT_PUBLIC_API_BASE_URL:-***REMOVED***}"
DB_URL="${SUPABASE_URL:-***REMOVED***}"

echo "📊 Environment: Staging"
echo "🏠 Frontend: $FRONTEND_URL"
echo "🔧 Backend: $API_URL"
echo "🗄️  Database: $DB_URL"
echo ""

# Check if we're in a local development context or cloud deployment
if [ -f "docker-compose.staging.yml" ]; then
    echo "1️⃣ Starting local staging environment with Docker..."
    docker-compose -f docker-compose.staging.yml up -d api worker
    
    # Wait for backend to be ready
    echo "2️⃣ Waiting for backend to be ready..."
    sleep 10
    curl -f "$API_URL/health" > /dev/null 2>&1 || echo "⚠️  Backend not ready yet, continuing..."
    
    echo ""
    echo "✅ Local staging environment started!"
    echo "🌐 Frontend: $FRONTEND_URL"
    echo "🔧 Backend: $API_URL"
    echo "🗄️  Database: $DB_URL"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
else
    echo "1️⃣ Staging environment is cloud-deployed"
    echo "2️⃣ Validating staging services..."
    
    # Test API health
    if curl -f "$API_URL/health" > /dev/null 2>&1; then
        echo "✅ API service is healthy"
    else
        echo "⚠️  API service may not be ready yet"
    fi
    
    # Test frontend accessibility
    if curl -f "$FRONTEND_URL" > /dev/null 2>&1; then
        echo "✅ Frontend is accessible"
    else
        echo "⚠️  Frontend may not be ready yet"
    fi
    
    echo ""
    echo "✅ Staging environment validation completed!"
    echo "🌐 Frontend: $FRONTEND_URL"
    echo "🔧 Backend: $API_URL"
    echo "🗄️  Database: $DB_URL"
    echo ""
    echo "Staging environment is ready for testing and validation."
fi